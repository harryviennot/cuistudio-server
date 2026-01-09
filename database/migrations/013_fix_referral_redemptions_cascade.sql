-- Migration: 013_fix_referral_redemptions_cascade
-- Description: Fix referral_redemptions foreign key to referral_codes to use ON DELETE CASCADE
-- Without this, deleting a user fails because:
-- 1. users deletion cascades to referral_codes
-- 2. But referral_redemptions.referral_code_id blocks the referral_codes deletion

-- Drop the existing constraint
ALTER TABLE public.referral_redemptions
    DROP CONSTRAINT IF EXISTS referral_redemptions_referral_code_id_fkey;

-- Re-add with ON DELETE CASCADE
ALTER TABLE public.referral_redemptions
    ADD CONSTRAINT referral_redemptions_referral_code_id_fkey
    FOREIGN KEY (referral_code_id) REFERENCES referral_codes(id) ON DELETE CASCADE;
