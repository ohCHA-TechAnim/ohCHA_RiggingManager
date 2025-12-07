/*
================================================================================
  Project:      ohCHA Rig Manager - HashTable Factory
  Description:  [v0.49] Fix: Used explicit dotNetObject constructor.
================================================================================
*/
(
    -- ✅ MaxScript에서 Hashtable을 생성하는 올바른 방법
    local new_hash_table = dotNetObject "System.Collections.Hashtable"
    new_hash_table
)