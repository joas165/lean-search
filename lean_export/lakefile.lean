import Lake
open Lake DSL

package lean_export

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

@[default_target]
lean_exe Dump where
  root := `Dump
