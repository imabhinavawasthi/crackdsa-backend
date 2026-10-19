-- ==============================================================================
-- CLEANUP SCRIPT: Remove Migrated expert_sheet Rows from practice_problems
--
-- This script removes only the 175 rows that were migrated from `expert_sheet`.
-- The original `expert_sheet` table remains 100% untouched and intact.
-- ==============================================================================

-- Step 1: Preview the count of rows that will be removed (should be exactly 175)
SELECT 
    COUNT(*) AS problems_to_remove
FROM public.practice_problems
WHERE (attributes->>'sheet_source') = 'expert_sheet'
   OR id IN (SELECT id FROM public.expert_sheet);

-- Step 2: Delete only those 175 migrated problems
DELETE FROM public.practice_problems
WHERE (attributes->>'sheet_source') = 'expert_sheet'
   OR id IN (SELECT id FROM public.expert_sheet);

-- Step 3: Verify remaining problems in practice_problems (should be 186 original problems)
SELECT 
    COUNT(*) AS remaining_practice_problems
FROM public.practice_problems;

-- Step 4: Verify expert_sheet table is intact (should still be 175)
SELECT 
    COUNT(*) AS expert_sheet_rows_intact
FROM public.expert_sheet;

-- Step 5 (Optional): If you want to delete the sheet entry from dsa_sheets:
-- DELETE FROM public.dsa_sheets WHERE id = 'newbie-to-expert-cp';
