-- Migration: 030_fix_user_deletion_foreign_keys
-- Description: Fix foreign key constraints that prevent user deletion
--
-- The error occurs because when auth.users is deleted, the CASCADE propagates to:
--   auth.users -> extraction_jobs (CASCADE)
-- But extraction_jobs cannot be deleted because credit_transactions still references it
-- and the FK constraint defaults to ON DELETE RESTRICT.
--
-- Similarly, content_reports.resolved_by references users.id without ON DELETE SET NULL.
--
-- Fix: Change these FK constraints to use ON DELETE SET NULL to preserve history
-- while allowing the referenced rows to be deleted.

-- ============================================================================
-- FIX 1: credit_transactions.extraction_job_id -> extraction_jobs.id
-- When extraction_job is deleted, set to NULL (preserves transaction history)
-- ============================================================================
ALTER TABLE public.credit_transactions
DROP CONSTRAINT IF EXISTS credit_transactions_extraction_job_id_fkey;

ALTER TABLE public.credit_transactions
ADD CONSTRAINT credit_transactions_extraction_job_id_fkey
FOREIGN KEY (extraction_job_id) REFERENCES public.extraction_jobs(id)
ON DELETE SET NULL;

-- ============================================================================
-- FIX 2: content_reports.resolved_by -> users.id
-- When admin user is deleted, set resolved_by to NULL (preserves report history)
-- ============================================================================
ALTER TABLE public.content_reports
DROP CONSTRAINT IF EXISTS content_reports_resolved_by_fkey;

ALTER TABLE public.content_reports
ADD CONSTRAINT content_reports_resolved_by_fkey
FOREIGN KEY (resolved_by) REFERENCES public.users(id)
ON DELETE SET NULL;

-- ============================================================================
-- FIX 3: extraction_feedback.resolved_by -> users.id
-- Same pattern for extraction feedback moderation
-- ============================================================================
ALTER TABLE public.extraction_feedback
DROP CONSTRAINT IF EXISTS extraction_feedback_resolved_by_fkey;

ALTER TABLE public.extraction_feedback
ADD CONSTRAINT extraction_feedback_resolved_by_fkey
FOREIGN KEY (resolved_by) REFERENCES public.users(id)
ON DELETE SET NULL;

-- ============================================================================
-- FIX 4: moderation_appeals.reviewed_by -> users.id
-- ============================================================================
ALTER TABLE public.moderation_appeals
DROP CONSTRAINT IF EXISTS moderation_appeals_reviewed_by_fkey;

ALTER TABLE public.moderation_appeals
ADD CONSTRAINT moderation_appeals_reviewed_by_fkey
FOREIGN KEY (reviewed_by) REFERENCES public.users(id)
ON DELETE SET NULL;

-- ============================================================================
-- FIX 5: user_warnings.issued_by -> users.id
-- ============================================================================
ALTER TABLE public.user_warnings
DROP CONSTRAINT IF EXISTS user_warnings_issued_by_fkey;

ALTER TABLE public.user_warnings
ADD CONSTRAINT user_warnings_issued_by_fkey
FOREIGN KEY (issued_by) REFERENCES public.users(id)
ON DELETE SET NULL;

-- ============================================================================
-- FIX 6: moderation_actions.moderator_id -> users.id
-- When moderator is deleted, preserve the action log but nullify the moderator
-- ============================================================================
ALTER TABLE public.moderation_actions
DROP CONSTRAINT IF EXISTS moderation_actions_moderator_id_fkey;

ALTER TABLE public.moderation_actions
ADD CONSTRAINT moderation_actions_moderator_id_fkey
FOREIGN KEY (moderator_id) REFERENCES public.users(id)
ON DELETE SET NULL;

-- ============================================================================
-- FIX 7: moderation_actions.target_user_id -> users.id
-- When target user is deleted, set to NULL (keeps action history)
-- ============================================================================
ALTER TABLE public.moderation_actions
DROP CONSTRAINT IF EXISTS moderation_actions_target_user_id_fkey;

ALTER TABLE public.moderation_actions
ADD CONSTRAINT moderation_actions_target_user_id_fkey
FOREIGN KEY (target_user_id) REFERENCES public.users(id)
ON DELETE SET NULL;
