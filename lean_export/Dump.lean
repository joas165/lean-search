import Lean
import Lean.Meta

open Lean System IO.FS Meta Core Json

-- Run inside MetaM to access the pretty printer (ppExpr)
def writeTheorems (filePath : String) : MetaM Unit := do
  IO.FS.createDirAll "data"
  let handle ← IO.FS.Handle.mk filePath Mode.write

  -- Write opening bracket
  handle.putStr "[\n"

  let env ← getEnv
  let mut isFirst := true
  let mut count := 0

  -- Iterate over constants
  for (name, cinfo) in env.constants do
    match cinfo with
    | .thmInfo info =>
      -- 1. PRETTY PRINTING (The Fix)
      -- ppExpr formats the type efficiently (respecting notation), avoiding memory explosion.
      let typeFmt ← ppExpr info.type
      let typeStr := toString typeFmt

      -- 2. JSON Construction
      let moduleName := name.getPrefix.toString
      let declName := name.toString

      let obj := Json.mkObj [
        ("name", Json.str declName),
        ("type", Json.str typeStr),
        ("module", Json.str moduleName)
      ]

      -- 3. Write to file
      if !isFirst then
        handle.putStr ",\n"
      isFirst := false

      handle.putStr ("  " ++ obj.compress)

      -- 4. Flush periodically
      count := count + 1
      if count % 5000 == 0 then
        IO.println s!"Processed {count} theorems..."
        handle.flush
    | _ => pure ()

  handle.putStr "\n]"
  IO.println s!"Done! Extracted {count} theorems."

def main : IO Unit := do
  IO.println "Initializing Mathlib environment..."

  -- Initialize search path
  initSearchPath (← findSysroot)

  -- Load Mathlib (This still takes ~4-6GB RAM)
  let env ← importModules #[{module := `Mathlib}] Options.empty

  IO.println "Extracting theorems..."

  -- Set up the Core Context to run MetaM
  let coreContext : Core.Context := {
    fileName := "<stdin>",
    fileMap := default
  }
  let coreState : Core.State := {
    env := env
  }

  -- Run the MetaM computation inside IO
  let _ ← (MetaM.run' (writeTheorems "data/decls.json")).toIO coreContext coreState
