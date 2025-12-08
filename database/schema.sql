--
-- PostgreSQL database dump
--

\restrict SNgc50alAw1GvG2FscR6NdlKLKXgc0M8dajlJTgU87a9VbhyiMR0Yt6ktvI8VPP

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.7 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP EVENT TRIGGER IF EXISTS pgrst_drop_watch;
DROP EVENT TRIGGER IF EXISTS pgrst_ddl_watch;
DROP EVENT TRIGGER IF EXISTS issue_pg_net_access;
DROP EVENT TRIGGER IF EXISTS issue_pg_graphql_access;
DROP EVENT TRIGGER IF EXISTS issue_pg_cron_access;
DROP EVENT TRIGGER IF EXISTS issue_graphql_placeholder;
DROP PUBLICATION IF EXISTS supabase_realtime;
DROP POLICY IF EXISTS "Users can upload recipe images" ON storage.objects;
DROP POLICY IF EXISTS "Users can upload cooking event images" ON storage.objects;
DROP POLICY IF EXISTS "Users can update their own recipe images" ON storage.objects;
DROP POLICY IF EXISTS "Users can update their own cooking event images" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete their own recipe images" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete their own cooking event images" ON storage.objects;
DROP POLICY IF EXISTS "Recipe images are publicly readable" ON storage.objects;
DROP POLICY IF EXISTS "Cooking event images are publicly readable" ON storage.objects;
DROP POLICY IF EXISTS "View public non-draft recipes" ON public.recipes;
DROP POLICY IF EXISTS "Video sources are public" ON public.video_sources;
DROP POLICY IF EXISTS "Video creators are public" ON public.video_creators;
DROP POLICY IF EXISTS "Users can view their own recipes including drafts" ON public.recipes;
DROP POLICY IF EXISTS "Users can view their own cookbooks" ON public.cookbooks;
DROP POLICY IF EXISTS "Users can view shares for their recipes" ON public.recipe_shares;
DROP POLICY IF EXISTS "Users can view shares for their cookbooks" ON public.cookbook_shares;
DROP POLICY IF EXISTS "Users can view shared recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can view shared cookbooks" ON public.cookbooks;
DROP POLICY IF EXISTS "Users can view own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can view own onboarding" ON public.user_onboarding;
DROP POLICY IF EXISTS "Users can view own cooking events" ON public.recipe_cooking_events;
DROP POLICY IF EXISTS "Users can view cooking events for public recipes" ON public.recipe_cooking_events;
DROP POLICY IF EXISTS "Users can update their own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can update their own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can update own onboarding" ON public.user_onboarding;
DROP POLICY IF EXISTS "Users can share their recipes" ON public.recipe_shares;
DROP POLICY IF EXISTS "Users can share their cookbooks" ON public.cookbook_shares;
DROP POLICY IF EXISTS "Users can manage their own recipe data" ON public.user_recipe_data;
DROP POLICY IF EXISTS "Users can manage their own extraction jobs" ON public.extraction_jobs;
DROP POLICY IF EXISTS "Users can manage their own cookbooks" ON public.cookbooks;
DROP POLICY IF EXISTS "Users can manage recipes in their folders" ON public.folder_recipes;
DROP POLICY IF EXISTS "Users can manage recipes in their cookbooks" ON public.cookbook_recipes;
DROP POLICY IF EXISTS "Users can manage folders in their cookbooks" ON public.cookbook_folders;
DROP POLICY IF EXISTS "Users can insert their own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can insert own preferences" ON public.user_preferences;
DROP POLICY IF EXISTS "Users can insert own onboarding" ON public.user_onboarding;
DROP POLICY IF EXISTS "Users can insert own cooking events" ON public.recipe_cooking_events;
DROP POLICY IF EXISTS "Users can delete their shares" ON public.recipe_shares;
DROP POLICY IF EXISTS "Users can delete their own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can delete their cookbook shares" ON public.cookbook_shares;
DROP POLICY IF EXISTS "Users can create their own profile" ON public.users;
DROP POLICY IF EXISTS "System can manage video sources" ON public.video_sources;
DROP POLICY IF EXISTS "System can manage video creators" ON public.video_creators;
DROP POLICY IF EXISTS "System can manage recipe contributors" ON public.recipe_contributors;
DROP POLICY IF EXISTS "Public recipes are viewable by everyone" ON public.recipes;
DROP POLICY IF EXISTS "Public cookbooks are viewable by everyone" ON public.cookbooks;
DROP POLICY IF EXISTS "Profiles are viewable by everyone" ON public.users;
DROP POLICY IF EXISTS "Everyone can view recipe contributors" ON public.recipe_contributors;
DROP POLICY IF EXISTS "Everyone can view featured recipes" ON public.featured_recipes;
DROP POLICY IF EXISTS "Collaborators can update shared recipes" ON public.recipes;
ALTER TABLE IF EXISTS ONLY storage.vector_indexes DROP CONSTRAINT IF EXISTS vector_indexes_bucket_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_upload_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_bucket_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads DROP CONSTRAINT IF EXISTS s3_multipart_uploads_bucket_id_fkey;
ALTER TABLE IF EXISTS ONLY storage.prefixes DROP CONSTRAINT IF EXISTS "prefixes_bucketId_fkey";
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS "objects_bucketId_fkey";
ALTER TABLE IF EXISTS ONLY public.video_sources DROP CONSTRAINT IF EXISTS video_sources_video_creator_id_fkey;
ALTER TABLE IF EXISTS ONLY public.video_sources DROP CONSTRAINT IF EXISTS video_sources_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_recipe_data DROP CONSTRAINT IF EXISTS user_recipe_data_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_recipe_data DROP CONSTRAINT IF EXISTS user_recipe_data_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_preferences DROP CONSTRAINT IF EXISTS user_preferences_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_onboarding DROP CONSTRAINT IF EXISTS user_onboarding_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipes DROP CONSTRAINT IF EXISTS recipes_original_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipes DROP CONSTRAINT IF EXISTS recipes_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_shares DROP CONSTRAINT IF EXISTS recipe_shares_shared_with_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_shares DROP CONSTRAINT IF EXISTS recipe_shares_shared_by_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_shares DROP CONSTRAINT IF EXISTS recipe_shares_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_cooking_events DROP CONSTRAINT IF EXISTS recipe_cooking_events_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_cooking_events DROP CONSTRAINT IF EXISTS recipe_cooking_events_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_contributors DROP CONSTRAINT IF EXISTS recipe_contributors_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_contributors DROP CONSTRAINT IF EXISTS recipe_contributors_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.folder_recipes DROP CONSTRAINT IF EXISTS folder_recipes_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.folder_recipes DROP CONSTRAINT IF EXISTS folder_recipes_folder_id_fkey;
ALTER TABLE IF EXISTS ONLY public.recipe_cooking_events DROP CONSTRAINT IF EXISTS fk_user;
ALTER TABLE IF EXISTS ONLY public.recipe_cooking_events DROP CONSTRAINT IF EXISTS fk_recipe;
ALTER TABLE IF EXISTS ONLY public.featured_recipes DROP CONSTRAINT IF EXISTS featured_recipes_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_existing_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbooks DROP CONSTRAINT IF EXISTS cookbooks_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_shares DROP CONSTRAINT IF EXISTS cookbook_shares_shared_with_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_shares DROP CONSTRAINT IF EXISTS cookbook_shares_shared_by_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_shares DROP CONSTRAINT IF EXISTS cookbook_shares_cookbook_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_recipes DROP CONSTRAINT IF EXISTS cookbook_recipes_recipe_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_recipes DROP CONSTRAINT IF EXISTS cookbook_recipes_cookbook_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_folders DROP CONSTRAINT IF EXISTS cookbook_folders_parent_folder_id_fkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_folders DROP CONSTRAINT IF EXISTS cookbook_folders_cookbook_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.sso_domains DROP CONSTRAINT IF EXISTS sso_domains_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.sessions DROP CONSTRAINT IF EXISTS sessions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.sessions DROP CONSTRAINT IF EXISTS sessions_oauth_client_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_flow_state_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_sso_provider_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_session_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.one_time_tokens DROP CONSTRAINT IF EXISTS one_time_tokens_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_client_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_client_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_user_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_challenges DROP CONSTRAINT IF EXISTS mfa_challenges_auth_factor_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS mfa_amr_claims_session_id_fkey;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_user_id_fkey;
DROP TRIGGER IF EXISTS update_objects_updated_at ON storage.objects;
DROP TRIGGER IF EXISTS prefixes_delete_hierarchy ON storage.prefixes;
DROP TRIGGER IF EXISTS prefixes_create_hierarchy ON storage.prefixes;
DROP TRIGGER IF EXISTS objects_update_create_prefix ON storage.objects;
DROP TRIGGER IF EXISTS objects_insert_create_prefix ON storage.objects;
DROP TRIGGER IF EXISTS objects_delete_delete_prefix ON storage.objects;
DROP TRIGGER IF EXISTS enforce_bucket_name_length_trigger ON storage.buckets;
DROP TRIGGER IF EXISTS tr_check_filters ON realtime.subscription;
DROP TRIGGER IF EXISTS update_video_sources_updated_at ON public.video_sources;
DROP TRIGGER IF EXISTS update_video_creators_updated_at ON public.video_creators;
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
DROP TRIGGER IF EXISTS update_user_recipe_data_updated_at ON public.user_recipe_data;
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON public.user_preferences;
DROP TRIGGER IF EXISTS update_recipes_updated_at ON public.recipes;
DROP TRIGGER IF EXISTS update_extraction_jobs_updated_at ON public.extraction_jobs;
DROP TRIGGER IF EXISTS update_cookbooks_updated_at ON public.cookbooks;
DROP TRIGGER IF EXISTS trigger_update_recipe_cooked_count ON public.user_recipe_data;
DROP TRIGGER IF EXISTS recipes_search_vector_trigger ON public.recipes;
DROP INDEX IF EXISTS storage.vector_indexes_name_bucket_id_idx;
DROP INDEX IF EXISTS storage.objects_bucket_id_level_idx;
DROP INDEX IF EXISTS storage.name_prefix_search;
DROP INDEX IF EXISTS storage.idx_prefixes_lower_name;
DROP INDEX IF EXISTS storage.idx_objects_lower_name;
DROP INDEX IF EXISTS storage.idx_objects_bucket_id_name;
DROP INDEX IF EXISTS storage.idx_name_bucket_level_unique;
DROP INDEX IF EXISTS storage.idx_multipart_uploads_list;
DROP INDEX IF EXISTS storage.buckets_analytics_unique_name_idx;
DROP INDEX IF EXISTS storage.bucketid_objname;
DROP INDEX IF EXISTS storage.bname;
DROP INDEX IF EXISTS realtime.subscription_subscription_id_entity_filters_key;
DROP INDEX IF EXISTS realtime.messages_inserted_at_topic_index;
DROP INDEX IF EXISTS realtime.ix_realtime_subscription_entity;
DROP INDEX IF EXISTS public.idx_waitlist_utm_source;
DROP INDEX IF EXISTS public.idx_waitlist_email;
DROP INDEX IF EXISTS public.idx_waitlist_created_at;
DROP INDEX IF EXISTS public.idx_video_sources_recipe;
DROP INDEX IF EXISTS public.idx_video_sources_platform;
DROP INDEX IF EXISTS public.idx_video_creators_platform;
DROP INDEX IF EXISTS public.idx_users_search;
DROP INDEX IF EXISTS public.idx_users_created_at;
DROP INDEX IF EXISTS public.idx_user_recipe_data_was_extracted;
DROP INDEX IF EXISTS public.idx_user_recipe_data_user_id;
DROP INDEX IF EXISTS public.idx_user_recipe_data_recipe_id;
DROP INDEX IF EXISTS public.idx_user_recipe_data_is_favorite;
DROP INDEX IF EXISTS public.idx_user_recipe_data_favorites;
DROP INDEX IF EXISTS public.idx_user_recipe_data_extracted;
DROP INDEX IF EXISTS public.idx_user_recipe_data_batch;
DROP INDEX IF EXISTS public.idx_user_preferences_user_id;
DROP INDEX IF EXISTS public.idx_user_onboarding_user_id;
DROP INDEX IF EXISTS public.idx_recipes_user_sort;
DROP INDEX IF EXISTS public.idx_recipes_total_times_cooked;
DROP INDEX IF EXISTS public.idx_recipes_title_search;
DROP INDEX IF EXISTS public.idx_recipes_tags_rating;
DROP INDEX IF EXISTS public.idx_recipes_tags;
DROP INDEX IF EXISTS public.idx_recipes_search_vector;
DROP INDEX IF EXISTS public.idx_recipes_public_sort;
DROP INDEX IF EXISTS public.idx_recipes_public_not_draft;
DROP INDEX IF EXISTS public.idx_recipes_original_recipe_id;
DROP INDEX IF EXISTS public.idx_recipes_is_public;
DROP INDEX IF EXISTS public.idx_recipes_is_draft;
DROP INDEX IF EXISTS public.idx_recipes_description_search;
DROP INDEX IF EXISTS public.idx_recipes_created_by_is_public;
DROP INDEX IF EXISTS public.idx_recipes_created_by;
DROP INDEX IF EXISTS public.idx_recipes_created_at;
DROP INDEX IF EXISTS public.idx_recipes_categories;
DROP INDEX IF EXISTS public.idx_recipes_average_rating;
DROP INDEX IF EXISTS public.idx_recipe_shares_shared_with_user_id;
DROP INDEX IF EXISTS public.idx_recipe_shares_recipe_id;
DROP INDEX IF EXISTS public.idx_recipe_contributors_user_id;
DROP INDEX IF EXISTS public.idx_recipe_contributors_unique;
DROP INDEX IF EXISTS public.idx_recipe_contributors_recipe_id;
DROP INDEX IF EXISTS public.idx_recipe_contributors_display_name;
DROP INDEX IF EXISTS public.idx_folder_recipes_recipe_id;
DROP INDEX IF EXISTS public.idx_folder_recipes_folder_id;
DROP INDEX IF EXISTS public.idx_featured_recipes_type;
DROP INDEX IF EXISTS public.idx_featured_recipes_recipe_id;
DROP INDEX IF EXISTS public.idx_featured_recipes_dates;
DROP INDEX IF EXISTS public.idx_extraction_jobs_user_id;
DROP INDEX IF EXISTS public.idx_extraction_jobs_status;
DROP INDEX IF EXISTS public.idx_extraction_jobs_source_urls;
DROP INDEX IF EXISTS public.idx_cooking_events_user_time;
DROP INDEX IF EXISTS public.idx_cooking_events_time_recipe;
DROP INDEX IF EXISTS public.idx_cooking_events_recipe_time;
DROP INDEX IF EXISTS public.idx_cookbooks_user_id;
DROP INDEX IF EXISTS public.idx_cookbooks_is_public;
DROP INDEX IF EXISTS public.idx_cookbook_shares_shared_with_user_id;
DROP INDEX IF EXISTS public.idx_cookbook_shares_cookbook_id;
DROP INDEX IF EXISTS public.idx_cookbook_recipes_recipe_id;
DROP INDEX IF EXISTS public.idx_cookbook_recipes_cookbook_id;
DROP INDEX IF EXISTS public.idx_cookbook_folders_parent_folder_id;
DROP INDEX IF EXISTS public.idx_cookbook_folders_cookbook_id;
DROP INDEX IF EXISTS auth.users_is_anonymous_idx;
DROP INDEX IF EXISTS auth.users_instance_id_idx;
DROP INDEX IF EXISTS auth.users_instance_id_email_idx;
DROP INDEX IF EXISTS auth.users_email_partial_key;
DROP INDEX IF EXISTS auth.user_id_created_at_idx;
DROP INDEX IF EXISTS auth.unique_phone_factor_per_user;
DROP INDEX IF EXISTS auth.sso_providers_resource_id_pattern_idx;
DROP INDEX IF EXISTS auth.sso_providers_resource_id_idx;
DROP INDEX IF EXISTS auth.sso_domains_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.sso_domains_domain_idx;
DROP INDEX IF EXISTS auth.sessions_user_id_idx;
DROP INDEX IF EXISTS auth.sessions_oauth_client_id_idx;
DROP INDEX IF EXISTS auth.sessions_not_after_idx;
DROP INDEX IF EXISTS auth.saml_relay_states_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.saml_relay_states_for_email_idx;
DROP INDEX IF EXISTS auth.saml_relay_states_created_at_idx;
DROP INDEX IF EXISTS auth.saml_providers_sso_provider_id_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_updated_at_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_session_id_revoked_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_parent_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_instance_id_user_id_idx;
DROP INDEX IF EXISTS auth.refresh_tokens_instance_id_idx;
DROP INDEX IF EXISTS auth.recovery_token_idx;
DROP INDEX IF EXISTS auth.reauthentication_token_idx;
DROP INDEX IF EXISTS auth.one_time_tokens_user_id_token_type_key;
DROP INDEX IF EXISTS auth.one_time_tokens_token_hash_hash_idx;
DROP INDEX IF EXISTS auth.one_time_tokens_relates_to_hash_idx;
DROP INDEX IF EXISTS auth.oauth_consents_user_order_idx;
DROP INDEX IF EXISTS auth.oauth_consents_active_user_client_idx;
DROP INDEX IF EXISTS auth.oauth_consents_active_client_idx;
DROP INDEX IF EXISTS auth.oauth_clients_deleted_at_idx;
DROP INDEX IF EXISTS auth.oauth_auth_pending_exp_idx;
DROP INDEX IF EXISTS auth.mfa_factors_user_id_idx;
DROP INDEX IF EXISTS auth.mfa_factors_user_friendly_name_unique;
DROP INDEX IF EXISTS auth.mfa_challenge_created_at_idx;
DROP INDEX IF EXISTS auth.idx_user_id_auth_method;
DROP INDEX IF EXISTS auth.idx_auth_code;
DROP INDEX IF EXISTS auth.identities_user_id_idx;
DROP INDEX IF EXISTS auth.identities_email_idx;
DROP INDEX IF EXISTS auth.flow_state_created_at_idx;
DROP INDEX IF EXISTS auth.factor_id_created_at_idx;
DROP INDEX IF EXISTS auth.email_change_token_new_idx;
DROP INDEX IF EXISTS auth.email_change_token_current_idx;
DROP INDEX IF EXISTS auth.confirmation_token_idx;
DROP INDEX IF EXISTS auth.audit_logs_instance_id_idx;
ALTER TABLE IF EXISTS ONLY supabase_migrations.schema_migrations DROP CONSTRAINT IF EXISTS schema_migrations_pkey;
ALTER TABLE IF EXISTS ONLY supabase_migrations.schema_migrations DROP CONSTRAINT IF EXISTS schema_migrations_idempotency_key_key;
ALTER TABLE IF EXISTS ONLY storage.vector_indexes DROP CONSTRAINT IF EXISTS vector_indexes_pkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads DROP CONSTRAINT IF EXISTS s3_multipart_uploads_pkey;
ALTER TABLE IF EXISTS ONLY storage.s3_multipart_uploads_parts DROP CONSTRAINT IF EXISTS s3_multipart_uploads_parts_pkey;
ALTER TABLE IF EXISTS ONLY storage.prefixes DROP CONSTRAINT IF EXISTS prefixes_pkey;
ALTER TABLE IF EXISTS ONLY storage.objects DROP CONSTRAINT IF EXISTS objects_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_pkey;
ALTER TABLE IF EXISTS ONLY storage.migrations DROP CONSTRAINT IF EXISTS migrations_name_key;
ALTER TABLE IF EXISTS ONLY storage.buckets_vectors DROP CONSTRAINT IF EXISTS buckets_vectors_pkey;
ALTER TABLE IF EXISTS ONLY storage.buckets DROP CONSTRAINT IF EXISTS buckets_pkey;
ALTER TABLE IF EXISTS ONLY storage.buckets_analytics DROP CONSTRAINT IF EXISTS buckets_analytics_pkey;
ALTER TABLE IF EXISTS ONLY realtime.schema_migrations DROP CONSTRAINT IF EXISTS schema_migrations_pkey;
ALTER TABLE IF EXISTS ONLY realtime.subscription DROP CONSTRAINT IF EXISTS pk_subscription;
ALTER TABLE IF EXISTS ONLY realtime.messages DROP CONSTRAINT IF EXISTS messages_pkey;
ALTER TABLE IF EXISTS ONLY public.waitlist DROP CONSTRAINT IF EXISTS waitlist_pkey;
ALTER TABLE IF EXISTS ONLY public.waitlist DROP CONSTRAINT IF EXISTS waitlist_email_key;
ALTER TABLE IF EXISTS ONLY public.video_sources DROP CONSTRAINT IF EXISTS video_sources_platform_platform_video_id_key;
ALTER TABLE IF EXISTS ONLY public.video_sources DROP CONSTRAINT IF EXISTS video_sources_pkey;
ALTER TABLE IF EXISTS ONLY public.video_creators DROP CONSTRAINT IF EXISTS video_creators_platform_platform_user_id_key;
ALTER TABLE IF EXISTS ONLY public.video_creators DROP CONSTRAINT IF EXISTS video_creators_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.user_recipe_data DROP CONSTRAINT IF EXISTS user_recipe_data_user_id_recipe_id_key;
ALTER TABLE IF EXISTS ONLY public.user_recipe_data DROP CONSTRAINT IF EXISTS user_recipe_data_pkey;
ALTER TABLE IF EXISTS ONLY public.user_preferences DROP CONSTRAINT IF EXISTS user_preferences_user_id_key;
ALTER TABLE IF EXISTS ONLY public.user_preferences DROP CONSTRAINT IF EXISTS user_preferences_pkey;
ALTER TABLE IF EXISTS ONLY public.user_onboarding DROP CONSTRAINT IF EXISTS user_onboarding_user_id_key;
ALTER TABLE IF EXISTS ONLY public.user_onboarding DROP CONSTRAINT IF EXISTS user_onboarding_pkey;
ALTER TABLE IF EXISTS ONLY public.recipes DROP CONSTRAINT IF EXISTS recipes_pkey;
ALTER TABLE IF EXISTS ONLY public.recipe_shares DROP CONSTRAINT IF EXISTS recipe_shares_recipe_id_shared_with_user_id_key;
ALTER TABLE IF EXISTS ONLY public.recipe_shares DROP CONSTRAINT IF EXISTS recipe_shares_pkey;
ALTER TABLE IF EXISTS ONLY public.recipe_cooking_events DROP CONSTRAINT IF EXISTS recipe_cooking_events_pkey;
ALTER TABLE IF EXISTS ONLY public.recipe_contributors DROP CONSTRAINT IF EXISTS recipe_contributors_pkey;
ALTER TABLE IF EXISTS ONLY public.folder_recipes DROP CONSTRAINT IF EXISTS folder_recipes_pkey;
ALTER TABLE IF EXISTS ONLY public.folder_recipes DROP CONSTRAINT IF EXISTS folder_recipes_folder_id_recipe_id_key;
ALTER TABLE IF EXISTS ONLY public.featured_recipes DROP CONSTRAINT IF EXISTS featured_recipes_pkey;
ALTER TABLE IF EXISTS ONLY public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_pkey;
ALTER TABLE IF EXISTS ONLY public.cookbooks DROP CONSTRAINT IF EXISTS cookbooks_pkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_shares DROP CONSTRAINT IF EXISTS cookbook_shares_pkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_shares DROP CONSTRAINT IF EXISTS cookbook_shares_cookbook_id_shared_with_user_id_key;
ALTER TABLE IF EXISTS ONLY public.cookbook_recipes DROP CONSTRAINT IF EXISTS cookbook_recipes_pkey;
ALTER TABLE IF EXISTS ONLY public.cookbook_recipes DROP CONSTRAINT IF EXISTS cookbook_recipes_cookbook_id_recipe_id_key;
ALTER TABLE IF EXISTS ONLY public.cookbook_folders DROP CONSTRAINT IF EXISTS cookbook_folders_pkey;
ALTER TABLE IF EXISTS ONLY auth.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY auth.users DROP CONSTRAINT IF EXISTS users_phone_key;
ALTER TABLE IF EXISTS ONLY auth.sso_providers DROP CONSTRAINT IF EXISTS sso_providers_pkey;
ALTER TABLE IF EXISTS ONLY auth.sso_domains DROP CONSTRAINT IF EXISTS sso_domains_pkey;
ALTER TABLE IF EXISTS ONLY auth.sessions DROP CONSTRAINT IF EXISTS sessions_pkey;
ALTER TABLE IF EXISTS ONLY auth.schema_migrations DROP CONSTRAINT IF EXISTS schema_migrations_pkey;
ALTER TABLE IF EXISTS ONLY auth.saml_relay_states DROP CONSTRAINT IF EXISTS saml_relay_states_pkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_pkey;
ALTER TABLE IF EXISTS ONLY auth.saml_providers DROP CONSTRAINT IF EXISTS saml_providers_entity_id_key;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_token_unique;
ALTER TABLE IF EXISTS ONLY auth.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_pkey;
ALTER TABLE IF EXISTS ONLY auth.one_time_tokens DROP CONSTRAINT IF EXISTS one_time_tokens_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_user_client_unique;
ALTER TABLE IF EXISTS ONLY auth.oauth_consents DROP CONSTRAINT IF EXISTS oauth_consents_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_clients DROP CONSTRAINT IF EXISTS oauth_clients_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_pkey;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_authorization_id_key;
ALTER TABLE IF EXISTS ONLY auth.oauth_authorizations DROP CONSTRAINT IF EXISTS oauth_authorizations_authorization_code_key;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_factors DROP CONSTRAINT IF EXISTS mfa_factors_last_challenged_at_key;
ALTER TABLE IF EXISTS ONLY auth.mfa_challenges DROP CONSTRAINT IF EXISTS mfa_challenges_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS mfa_amr_claims_session_id_authentication_method_pkey;
ALTER TABLE IF EXISTS ONLY auth.instances DROP CONSTRAINT IF EXISTS instances_pkey;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_provider_id_provider_unique;
ALTER TABLE IF EXISTS ONLY auth.identities DROP CONSTRAINT IF EXISTS identities_pkey;
ALTER TABLE IF EXISTS ONLY auth.flow_state DROP CONSTRAINT IF EXISTS flow_state_pkey;
ALTER TABLE IF EXISTS ONLY auth.audit_log_entries DROP CONSTRAINT IF EXISTS audit_log_entries_pkey;
ALTER TABLE IF EXISTS ONLY auth.mfa_amr_claims DROP CONSTRAINT IF EXISTS amr_id_pk;
ALTER TABLE IF EXISTS auth.refresh_tokens ALTER COLUMN id DROP DEFAULT;
DROP TABLE IF EXISTS supabase_migrations.schema_migrations;
DROP TABLE IF EXISTS storage.vector_indexes;
DROP TABLE IF EXISTS storage.s3_multipart_uploads_parts;
DROP TABLE IF EXISTS storage.s3_multipart_uploads;
DROP TABLE IF EXISTS storage.prefixes;
DROP TABLE IF EXISTS storage.objects;
DROP TABLE IF EXISTS storage.migrations;
DROP TABLE IF EXISTS storage.buckets_vectors;
DROP TABLE IF EXISTS storage.buckets_analytics;
DROP TABLE IF EXISTS storage.buckets;
DROP TABLE IF EXISTS realtime.subscription;
DROP TABLE IF EXISTS realtime.schema_migrations;
DROP TABLE IF EXISTS realtime.messages;
DROP TABLE IF EXISTS public.waitlist;
DROP TABLE IF EXISTS public.video_sources;
DROP TABLE IF EXISTS public.video_creators;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.user_recipe_data;
DROP TABLE IF EXISTS public.user_preferences;
DROP TABLE IF EXISTS public.user_onboarding;
DROP TABLE IF EXISTS public.recipes;
DROP TABLE IF EXISTS public.recipe_shares;
DROP TABLE IF EXISTS public.recipe_cooking_events;
DROP TABLE IF EXISTS public.recipe_contributors;
DROP TABLE IF EXISTS public.folder_recipes;
DROP TABLE IF EXISTS public.featured_recipes;
DROP TABLE IF EXISTS public.cookbooks;
DROP TABLE IF EXISTS public.cookbook_shares;
DROP TABLE IF EXISTS public.cookbook_recipes;
DROP TABLE IF EXISTS public.cookbook_folders;
DROP TABLE IF EXISTS auth.users;
DROP TABLE IF EXISTS auth.sso_providers;
DROP TABLE IF EXISTS auth.sso_domains;
DROP TABLE IF EXISTS auth.sessions;
DROP TABLE IF EXISTS auth.schema_migrations;
DROP TABLE IF EXISTS auth.saml_relay_states;
DROP TABLE IF EXISTS auth.saml_providers;
DROP SEQUENCE IF EXISTS auth.refresh_tokens_id_seq;
DROP TABLE IF EXISTS auth.refresh_tokens;
DROP TABLE IF EXISTS auth.one_time_tokens;
DROP TABLE IF EXISTS auth.oauth_consents;
DROP TABLE IF EXISTS auth.oauth_clients;
DROP TABLE IF EXISTS auth.oauth_authorizations;
DROP TABLE IF EXISTS auth.mfa_factors;
DROP TABLE IF EXISTS auth.mfa_challenges;
DROP TABLE IF EXISTS auth.mfa_amr_claims;
DROP TABLE IF EXISTS auth.instances;
DROP TABLE IF EXISTS auth.identities;
DROP TABLE IF EXISTS auth.flow_state;
DROP TABLE IF EXISTS auth.audit_log_entries;
DROP FUNCTION IF EXISTS storage.update_updated_at_column();
DROP FUNCTION IF EXISTS storage.search_v2(prefix text, bucket_name text, limits integer, levels integer, start_after text, sort_order text, sort_column text, sort_column_after text);
DROP FUNCTION IF EXISTS storage.search_v1_optimised(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.search_legacy_v1(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.search(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text);
DROP FUNCTION IF EXISTS storage.prefixes_insert_trigger();
DROP FUNCTION IF EXISTS storage.prefixes_delete_cleanup();
DROP FUNCTION IF EXISTS storage.operation();
DROP FUNCTION IF EXISTS storage.objects_update_prefix_trigger();
DROP FUNCTION IF EXISTS storage.objects_update_level_trigger();
DROP FUNCTION IF EXISTS storage.objects_update_cleanup();
DROP FUNCTION IF EXISTS storage.objects_insert_prefix_trigger();
DROP FUNCTION IF EXISTS storage.objects_delete_cleanup();
DROP FUNCTION IF EXISTS storage.lock_top_prefixes(bucket_ids text[], names text[]);
DROP FUNCTION IF EXISTS storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, start_after text, next_token text);
DROP FUNCTION IF EXISTS storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, next_key_token text, next_upload_token text);
DROP FUNCTION IF EXISTS storage.get_size_by_bucket();
DROP FUNCTION IF EXISTS storage.get_prefixes(name text);
DROP FUNCTION IF EXISTS storage.get_prefix(name text);
DROP FUNCTION IF EXISTS storage.get_level(name text);
DROP FUNCTION IF EXISTS storage.foldername(name text);
DROP FUNCTION IF EXISTS storage.filename(name text);
DROP FUNCTION IF EXISTS storage.extension(name text);
DROP FUNCTION IF EXISTS storage.enforce_bucket_name_length();
DROP FUNCTION IF EXISTS storage.delete_prefix_hierarchy_trigger();
DROP FUNCTION IF EXISTS storage.delete_prefix(_bucket_id text, _name text);
DROP FUNCTION IF EXISTS storage.delete_leaf_prefixes(bucket_ids text[], names text[]);
DROP FUNCTION IF EXISTS storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb);
DROP FUNCTION IF EXISTS storage.add_prefixes(_bucket_id text, _name text);
DROP FUNCTION IF EXISTS realtime.topic();
DROP FUNCTION IF EXISTS realtime.to_regrole(role_name text);
DROP FUNCTION IF EXISTS realtime.subscription_check_filters();
DROP FUNCTION IF EXISTS realtime.send(payload jsonb, event text, topic text, private boolean);
DROP FUNCTION IF EXISTS realtime.quote_wal2json(entity regclass);
DROP FUNCTION IF EXISTS realtime.list_changes(publication name, slot_name name, max_changes integer, max_record_bytes integer);
DROP FUNCTION IF EXISTS realtime.is_visible_through_filters(columns realtime.wal_column[], filters realtime.user_defined_filter[]);
DROP FUNCTION IF EXISTS realtime.check_equality_op(op realtime.equality_op, type_ regtype, val_1 text, val_2 text);
DROP FUNCTION IF EXISTS realtime."cast"(val text, type_ regtype);
DROP FUNCTION IF EXISTS realtime.build_prepared_statement_sql(prepared_statement_name text, entity regclass, columns realtime.wal_column[]);
DROP FUNCTION IF EXISTS realtime.broadcast_changes(topic_name text, event_name text, operation text, table_name text, table_schema text, new record, old record, level text);
DROP FUNCTION IF EXISTS realtime.apply_rls(wal jsonb, max_record_bytes integer);
DROP FUNCTION IF EXISTS public.validate_instruction_format(instruction jsonb);
DROP FUNCTION IF EXISTS public.update_updated_at_column();
DROP FUNCTION IF EXISTS public.update_recipe_cooked_count();
DROP FUNCTION IF EXISTS public.search_recipes_full_text(search_query text, user_id_param uuid, limit_param integer, offset_param integer);
DROP FUNCTION IF EXISTS public.recipes_search_vector_update();
DROP FUNCTION IF EXISTS public.migrate_instructions_array(instructions jsonb);
DROP FUNCTION IF EXISTS public.migrate_instruction(instruction jsonb);
DROP FUNCTION IF EXISTS public.is_user_anonymous(user_id uuid);
DROP FUNCTION IF EXISTS public.get_user_cooking_history(user_id_param uuid, time_window_days integer, limit_param integer, offset_param integer);
DROP FUNCTION IF EXISTS public.get_trending_recipes(time_window_days integer, limit_param integer, offset_param integer);
DROP FUNCTION IF EXISTS public.get_most_extracted_website_recipes(limit_param integer, offset_param integer);
DROP FUNCTION IF EXISTS public.get_most_extracted_video_recipes(limit_param integer, offset_param integer);
DROP FUNCTION IF EXISTS public.get_first_source_url(job public.extraction_jobs);
DROP TABLE IF EXISTS public.extraction_jobs;
DROP FUNCTION IF EXISTS public.generate_recipe_image_path(user_id uuid, file_extension text);
DROP FUNCTION IF EXISTS public.generate_cooking_event_image_path(user_id uuid, event_id uuid, file_extension text);
DROP FUNCTION IF EXISTS public.count_source_urls(job_id uuid);
DROP FUNCTION IF EXISTS public.calculate_average_rating(distribution jsonb);
DROP FUNCTION IF EXISTS pgbouncer.get_auth(p_usename text);
DROP FUNCTION IF EXISTS extensions.set_graphql_placeholder();
DROP FUNCTION IF EXISTS extensions.pgrst_drop_watch();
DROP FUNCTION IF EXISTS extensions.pgrst_ddl_watch();
DROP FUNCTION IF EXISTS extensions.grant_pg_net_access();
DROP FUNCTION IF EXISTS extensions.grant_pg_graphql_access();
DROP FUNCTION IF EXISTS extensions.grant_pg_cron_access();
DROP FUNCTION IF EXISTS auth.uid();
DROP FUNCTION IF EXISTS auth.role();
DROP FUNCTION IF EXISTS auth.jwt();
DROP FUNCTION IF EXISTS auth.email();
DROP TYPE IF EXISTS storage.buckettype;
DROP TYPE IF EXISTS realtime.wal_rls;
DROP TYPE IF EXISTS realtime.wal_column;
DROP TYPE IF EXISTS realtime.user_defined_filter;
DROP TYPE IF EXISTS realtime.equality_op;
DROP TYPE IF EXISTS realtime.action;
DROP TYPE IF EXISTS auth.one_time_token_type;
DROP TYPE IF EXISTS auth.oauth_response_type;
DROP TYPE IF EXISTS auth.oauth_registration_type;
DROP TYPE IF EXISTS auth.oauth_client_type;
DROP TYPE IF EXISTS auth.oauth_authorization_status;
DROP TYPE IF EXISTS auth.factor_type;
DROP TYPE IF EXISTS auth.factor_status;
DROP TYPE IF EXISTS auth.code_challenge_method;
DROP TYPE IF EXISTS auth.aal_level;
DROP EXTENSION IF EXISTS "uuid-ossp";
DROP EXTENSION IF EXISTS supabase_vault;
DROP EXTENSION IF EXISTS pgcrypto;
DROP EXTENSION IF EXISTS pg_stat_statements;
DROP EXTENSION IF EXISTS pg_graphql;
DROP EXTENSION IF EXISTS index_advisor;
DROP EXTENSION IF EXISTS hypopg;
DROP SCHEMA IF EXISTS vault;
DROP SCHEMA IF EXISTS supabase_migrations;
DROP SCHEMA IF EXISTS storage;
DROP SCHEMA IF EXISTS realtime;
DROP SCHEMA IF EXISTS pgbouncer;
DROP SCHEMA IF EXISTS graphql_public;
DROP SCHEMA IF EXISTS graphql;
DROP SCHEMA IF EXISTS extensions;
DROP SCHEMA IF EXISTS auth;
--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- Name: extensions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA extensions;


--
-- Name: graphql; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql;


--
-- Name: graphql_public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql_public;


--
-- Name: pgbouncer; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pgbouncer;


--
-- Name: realtime; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA realtime;


--
-- Name: storage; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA storage;


--
-- Name: supabase_migrations; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA supabase_migrations;


--
-- Name: vault; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA vault;


--
-- Name: hypopg; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS hypopg WITH SCHEMA extensions;


--
-- Name: EXTENSION hypopg; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION hypopg IS 'Hypothetical indexes for PostgreSQL';


--
-- Name: index_advisor; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS index_advisor WITH SCHEMA extensions;


--
-- Name: EXTENSION index_advisor; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION index_advisor IS 'Query index advisor';


--
-- Name: pg_graphql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_graphql WITH SCHEMA graphql;


--
-- Name: EXTENSION pg_graphql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_graphql IS 'pg_graphql: GraphQL support';


--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: supabase_vault; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS supabase_vault WITH SCHEMA vault;


--
-- Name: EXTENSION supabase_vault; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION supabase_vault IS 'Supabase Vault Extension';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: aal_level; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.aal_level AS ENUM (
    'aal1',
    'aal2',
    'aal3'
);


--
-- Name: code_challenge_method; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.code_challenge_method AS ENUM (
    's256',
    'plain'
);


--
-- Name: factor_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_status AS ENUM (
    'unverified',
    'verified'
);


--
-- Name: factor_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_type AS ENUM (
    'totp',
    'webauthn',
    'phone'
);


--
-- Name: oauth_authorization_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_authorization_status AS ENUM (
    'pending',
    'approved',
    'denied',
    'expired'
);


--
-- Name: oauth_client_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_client_type AS ENUM (
    'public',
    'confidential'
);


--
-- Name: oauth_registration_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_registration_type AS ENUM (
    'dynamic',
    'manual'
);


--
-- Name: oauth_response_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_response_type AS ENUM (
    'code'
);


--
-- Name: one_time_token_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.one_time_token_type AS ENUM (
    'confirmation_token',
    'reauthentication_token',
    'recovery_token',
    'email_change_token_new',
    'email_change_token_current',
    'phone_change_token'
);


--
-- Name: action; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.action AS ENUM (
    'INSERT',
    'UPDATE',
    'DELETE',
    'TRUNCATE',
    'ERROR'
);


--
-- Name: equality_op; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.equality_op AS ENUM (
    'eq',
    'neq',
    'lt',
    'lte',
    'gt',
    'gte',
    'in'
);


--
-- Name: user_defined_filter; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.user_defined_filter AS (
	column_name text,
	op realtime.equality_op,
	value text
);


--
-- Name: wal_column; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_column AS (
	name text,
	type_name text,
	type_oid oid,
	value jsonb,
	is_pkey boolean,
	is_selectable boolean
);


--
-- Name: wal_rls; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_rls AS (
	wal jsonb,
	is_rls_enabled boolean,
	subscription_ids uuid[],
	errors text[]
);


--
-- Name: buckettype; Type: TYPE; Schema: storage; Owner: -
--

CREATE TYPE storage.buckettype AS ENUM (
    'STANDARD',
    'ANALYTICS',
    'VECTOR'
);


--
-- Name: email(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.email() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text
$$;


--
-- Name: FUNCTION email(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.email() IS 'Deprecated. Use auth.jwt() -> ''email'' instead.';


--
-- Name: jwt(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.jwt() RETURNS jsonb
    LANGUAGE sql STABLE
    AS $$
  select 
    coalesce(
        nullif(current_setting('request.jwt.claim', true), ''),
        nullif(current_setting('request.jwt.claims', true), '')
    )::jsonb
$$;


--
-- Name: role(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.role() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;


--
-- Name: FUNCTION role(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.role() IS 'Deprecated. Use auth.jwt() -> ''role'' instead.';


--
-- Name: uid(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;


--
-- Name: FUNCTION uid(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.uid() IS 'Deprecated. Use auth.jwt() -> ''sub'' instead.';


--
-- Name: grant_pg_cron_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_cron_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_cron'
  )
  THEN
    grant usage on schema cron to postgres with grant option;

    alter default privileges in schema cron grant all on tables to postgres with grant option;
    alter default privileges in schema cron grant all on functions to postgres with grant option;
    alter default privileges in schema cron grant all on sequences to postgres with grant option;

    alter default privileges for user supabase_admin in schema cron grant all
        on sequences to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on tables to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on functions to postgres with grant option;

    grant all privileges on all tables in schema cron to postgres with grant option;
    revoke all on table cron.job from postgres;
    grant select on table cron.job to postgres with grant option;
  END IF;
END;
$$;


--
-- Name: FUNCTION grant_pg_cron_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_cron_access() IS 'Grants access to pg_cron';


--
-- Name: grant_pg_graphql_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_graphql_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
DECLARE
    func_is_graphql_resolve bool;
BEGIN
    func_is_graphql_resolve = (
        SELECT n.proname = 'resolve'
        FROM pg_event_trigger_ddl_commands() AS ev
        LEFT JOIN pg_catalog.pg_proc AS n
        ON ev.objid = n.oid
    );

    IF func_is_graphql_resolve
    THEN
        -- Update public wrapper to pass all arguments through to the pg_graphql resolve func
        DROP FUNCTION IF EXISTS graphql_public.graphql;
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language sql
        as $$
            select graphql.resolve(
                query := query,
                variables := coalesce(variables, '{}'),
                "operationName" := "operationName",
                extensions := extensions
            );
        $$;

        -- This hook executes when `graphql.resolve` is created. That is not necessarily the last
        -- function in the extension so we need to grant permissions on existing entities AND
        -- update default permissions to any others that are created after `graphql.resolve`
        grant usage on schema graphql to postgres, anon, authenticated, service_role;
        grant select on all tables in schema graphql to postgres, anon, authenticated, service_role;
        grant execute on all functions in schema graphql to postgres, anon, authenticated, service_role;
        grant all on all sequences in schema graphql to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on tables to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on functions to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on sequences to postgres, anon, authenticated, service_role;

        -- Allow postgres role to allow granting usage on graphql and graphql_public schemas to custom roles
        grant usage on schema graphql_public to postgres with grant option;
        grant usage on schema graphql to postgres with grant option;
    END IF;

END;
$_$;


--
-- Name: FUNCTION grant_pg_graphql_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_graphql_access() IS 'Grants access to pg_graphql';


--
-- Name: grant_pg_net_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_net_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_net'
  )
  THEN
    IF NOT EXISTS (
      SELECT 1
      FROM pg_roles
      WHERE rolname = 'supabase_functions_admin'
    )
    THEN
      CREATE USER supabase_functions_admin NOINHERIT CREATEROLE LOGIN NOREPLICATION;
    END IF;

    GRANT USAGE ON SCHEMA net TO supabase_functions_admin, postgres, anon, authenticated, service_role;

    IF EXISTS (
      SELECT FROM pg_extension
      WHERE extname = 'pg_net'
      -- all versions in use on existing projects as of 2025-02-20
      -- version 0.12.0 onwards don't need these applied
      AND extversion IN ('0.2', '0.6', '0.7', '0.7.1', '0.8', '0.10.0', '0.11.0')
    ) THEN
      ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;
      ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;

      ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;
      ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;

      REVOKE ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;
      REVOKE ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;

      GRANT EXECUTE ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
      GRANT EXECUTE ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
    END IF;
  END IF;
END;
$$;


--
-- Name: FUNCTION grant_pg_net_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_net_access() IS 'Grants access to pg_net';


--
-- Name: pgrst_ddl_watch(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.pgrst_ddl_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands()
  LOOP
    IF cmd.command_tag IN (
      'CREATE SCHEMA', 'ALTER SCHEMA'
    , 'CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO', 'ALTER TABLE'
    , 'CREATE FOREIGN TABLE', 'ALTER FOREIGN TABLE'
    , 'CREATE VIEW', 'ALTER VIEW'
    , 'CREATE MATERIALIZED VIEW', 'ALTER MATERIALIZED VIEW'
    , 'CREATE FUNCTION', 'ALTER FUNCTION'
    , 'CREATE TRIGGER'
    , 'CREATE TYPE', 'ALTER TYPE'
    , 'CREATE RULE'
    , 'COMMENT'
    )
    -- don't notify in case of CREATE TEMP table or other objects created on pg_temp
    AND cmd.schema_name is distinct from 'pg_temp'
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


--
-- Name: pgrst_drop_watch(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.pgrst_drop_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  obj record;
BEGIN
  FOR obj IN SELECT * FROM pg_event_trigger_dropped_objects()
  LOOP
    IF obj.object_type IN (
      'schema'
    , 'table'
    , 'foreign table'
    , 'view'
    , 'materialized view'
    , 'function'
    , 'trigger'
    , 'type'
    , 'rule'
    )
    AND obj.is_temporary IS false -- no pg_temp objects
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


--
-- Name: set_graphql_placeholder(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.set_graphql_placeholder() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
    DECLARE
    graphql_is_dropped bool;
    BEGIN
    graphql_is_dropped = (
        SELECT ev.schema_name = 'graphql_public'
        FROM pg_event_trigger_dropped_objects() AS ev
        WHERE ev.schema_name = 'graphql_public'
    );

    IF graphql_is_dropped
    THEN
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language plpgsql
        as $$
            DECLARE
                server_version float;
            BEGIN
                server_version = (SELECT (SPLIT_PART((select version()), ' ', 2))::float);

                IF server_version >= 14 THEN
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql extension is not enabled.'
                            )
                        )
                    );
                ELSE
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql is only available on projects running Postgres 14 onwards.'
                            )
                        )
                    );
                END IF;
            END;
        $$;
    END IF;

    END;
$_$;


--
-- Name: FUNCTION set_graphql_placeholder(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.set_graphql_placeholder() IS 'Reintroduces placeholder function for graphql_public.graphql';


--
-- Name: get_auth(text); Type: FUNCTION; Schema: pgbouncer; Owner: -
--

CREATE FUNCTION pgbouncer.get_auth(p_usename text) RETURNS TABLE(username text, password text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $_$
begin
    raise debug 'PgBouncer auth request: %', p_usename;

    return query
    select 
        rolname::text, 
        case when rolvaliduntil < now() 
            then null 
            else rolpassword::text 
        end 
    from pg_authid 
    where rolname=$1 and rolcanlogin;
end;
$_$;


--
-- Name: calculate_average_rating(jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.calculate_average_rating(distribution jsonb) RETURNS numeric
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
  total_ratings INTEGER;
  weighted_sum DECIMAL;
BEGIN
  -- Calculate total number of ratings (all half-star levels)
  total_ratings :=
    (distribution->>'0.5')::INTEGER +
    (distribution->>'1')::INTEGER +
    (distribution->>'1.5')::INTEGER +
    (distribution->>'2')::INTEGER +
    (distribution->>'2.5')::INTEGER +
    (distribution->>'3')::INTEGER +
    (distribution->>'3.5')::INTEGER +
    (distribution->>'4')::INTEGER +
    (distribution->>'4.5')::INTEGER +
    (distribution->>'5')::INTEGER;

  -- Return NULL if no ratings
  IF total_ratings = 0 THEN
    RETURN NULL;
  END IF;

  -- Calculate weighted sum with half-star precision
  weighted_sum :=
    0.5 * (distribution->>'0.5')::INTEGER +
    1.0 * (distribution->>'1')::INTEGER +
    1.5 * (distribution->>'1.5')::INTEGER +
    2.0 * (distribution->>'2')::INTEGER +
    2.5 * (distribution->>'2.5')::INTEGER +
    3.0 * (distribution->>'3')::INTEGER +
    3.5 * (distribution->>'3.5')::INTEGER +
    4.0 * (distribution->>'4')::INTEGER +
    4.5 * (distribution->>'4.5')::INTEGER +
    5.0 * (distribution->>'5')::INTEGER;

  -- Return average rounded to 2 decimal places
  RETURN ROUND(weighted_sum::DECIMAL / total_ratings, 2);
END;
$$;


--
-- Name: FUNCTION calculate_average_rating(distribution jsonb); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.calculate_average_rating(distribution jsonb) IS 'Helper function to calculate average rating from distribution JSONB with half-star support (0.5-5.0). Returns NULL if no ratings.';


--
-- Name: count_source_urls(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.count_source_urls(job_id uuid) RETURNS integer
    LANGUAGE sql STABLE
    AS $$
    SELECT jsonb_array_length(source_urls)
    FROM extraction_jobs
    WHERE id = job_id;
$$;


--
-- Name: FUNCTION count_source_urls(job_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.count_source_urls(job_id uuid) IS 'Returns the number of source images in an extraction job';


--
-- Name: generate_cooking_event_image_path(uuid, uuid, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.generate_cooking_event_image_path(user_id uuid, event_id uuid, file_extension text) RETURNS text
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN user_id::text || '/' || event_id::text || '.' || file_extension;
END;
$$;


--
-- Name: FUNCTION generate_cooking_event_image_path(user_id uuid, event_id uuid, file_extension text); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.generate_cooking_event_image_path(user_id uuid, event_id uuid, file_extension text) IS 'Generates a unique storage path for cooking event images in format: {user_id}/{event_id}.{extension}';


--
-- Name: generate_recipe_image_path(uuid, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.generate_recipe_image_path(user_id uuid, file_extension text) RETURNS text
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN user_id::text || '/' || gen_random_uuid()::text || '.' || file_extension;
END;
$$;


--
-- Name: FUNCTION generate_recipe_image_path(user_id uuid, file_extension text); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.generate_recipe_image_path(user_id uuid, file_extension text) IS 'Generates a unique storage path for recipe images in format: {user_id}/{uuid}.{extension}';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: extraction_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.extraction_jobs (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    source_type character varying(20) NOT NULL,
    source_url text,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    recipe_id uuid,
    error_message text,
    progress_percentage integer DEFAULT 0,
    current_step character varying(200),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    source_urls jsonb DEFAULT '[]'::jsonb,
    existing_recipe_id uuid,
    CONSTRAINT extraction_jobs_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['video'::character varying, 'photo'::character varying, 'voice'::character varying, 'url'::character varying, 'paste'::character varying, 'link'::character varying])::text[]))),
    CONSTRAINT extraction_jobs_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying, 'not_a_recipe'::character varying, 'website_blocked'::character varying])::text[]))),
    CONSTRAINT source_urls_is_array CHECK ((jsonb_typeof(source_urls) = 'array'::text)),
    CONSTRAINT source_urls_max_length CHECK ((jsonb_array_length(source_urls) <= 5))
);


--
-- Name: COLUMN extraction_jobs.source_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.extraction_jobs.source_url IS 'DEPRECATED: Use source_urls array instead. Kept for backward compatibility.';


--
-- Name: COLUMN extraction_jobs.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.extraction_jobs.status IS 'Job status: pending (waiting), processing (in progress), completed (success), failed (error), not_a_recipe (content does not contain a recipe)';


--
-- Name: COLUMN extraction_jobs.source_urls; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.extraction_jobs.source_urls IS 'Array of source image URLs for multi-image recipe extraction. Max 5 images per job.';


--
-- Name: COLUMN extraction_jobs.existing_recipe_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.extraction_jobs.existing_recipe_id IS 'References an existing recipe when duplicate video is detected during extraction';


--
-- Name: get_first_source_url(public.extraction_jobs); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_first_source_url(job public.extraction_jobs) RETURNS text
    LANGUAGE sql STABLE
    AS $$
    SELECT source_urls->>0 FROM extraction_jobs WHERE id = job.id;
$$;


--
-- Name: FUNCTION get_first_source_url(job public.extraction_jobs); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_first_source_url(job public.extraction_jobs) IS 'Helper function to get the first source URL from source_urls array for backward compatibility';


--
-- Name: get_most_extracted_video_recipes(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_most_extracted_video_recipes(limit_param integer DEFAULT 8, offset_param integer DEFAULT 0) RETURNS TABLE(recipe_id uuid, extraction_count bigint, unique_extractors bigint)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id as recipe_id,
        COUNT(DISTINCT urd.user_id) as extraction_count,
        COUNT(DISTINCT urd.user_id) as unique_extractors
    FROM recipes r
    INNER JOIN video_sources vs ON vs.recipe_id = r.id
    INNER JOIN user_recipe_data urd ON urd.recipe_id = r.id AND urd.was_extracted = true
    WHERE r.is_public = true AND r.is_draft = false
    GROUP BY r.id
    HAVING COUNT(DISTINCT urd.user_id) >= 1
    ORDER BY extraction_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;


--
-- Name: FUNCTION get_most_extracted_video_recipes(limit_param integer, offset_param integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_most_extracted_video_recipes(limit_param integer, offset_param integer) IS 'Returns video-sourced recipes (TikTok, Instagram, YouTube) ordered by extraction count.
Used for "Trending on Socials" discovery section.';


--
-- Name: get_most_extracted_website_recipes(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_most_extracted_website_recipes(limit_param integer DEFAULT 8, offset_param integer DEFAULT 0) RETURNS TABLE(recipe_id uuid, extraction_count bigint, unique_extractors bigint)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id as recipe_id,
        COUNT(DISTINCT urd.user_id) as extraction_count,
        COUNT(DISTINCT urd.user_id) as unique_extractors
    FROM recipes r
    INNER JOIN user_recipe_data urd ON urd.recipe_id = r.id AND urd.was_extracted = true
    WHERE r.is_public = true
      AND r.is_draft = false
      AND r.source_type = 'link'
      AND NOT EXISTS (
          SELECT 1 FROM video_sources vs WHERE vs.recipe_id = r.id
      )
    GROUP BY r.id
    HAVING COUNT(DISTINCT urd.user_id) >= 1
    ORDER BY extraction_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;


--
-- Name: FUNCTION get_most_extracted_website_recipes(limit_param integer, offset_param integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_most_extracted_website_recipes(limit_param integer, offset_param integer) IS 'Returns website-sourced recipes (not from video platforms) ordered by extraction count.
Used for "Popular Recipes Online" discovery section.';


--
-- Name: get_trending_recipes(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_trending_recipes(time_window_days integer DEFAULT 7, limit_param integer DEFAULT 20, offset_param integer DEFAULT 0) RETURNS TABLE(recipe_id uuid, cook_count bigint, unique_users bigint)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        rce.recipe_id,
        COUNT(*) as cook_count,
        COUNT(DISTINCT rce.user_id) as unique_users
    FROM recipe_cooking_events rce
    INNER JOIN recipes r ON r.id = rce.recipe_id
    WHERE
        rce.cooked_at >= NOW() - INTERVAL '1 day' * time_window_days
        AND r.is_public = true
    GROUP BY rce.recipe_id
    ORDER BY cook_count DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;


--
-- Name: FUNCTION get_trending_recipes(time_window_days integer, limit_param integer, offset_param integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_trending_recipes(time_window_days integer, limit_param integer, offset_param integer) IS 'Returns recipes ordered by cooking frequency in the specified time window. Includes cook count and unique user count.';


--
-- Name: get_user_cooking_history(uuid, integer, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_user_cooking_history(user_id_param uuid, time_window_days integer DEFAULT 365, limit_param integer DEFAULT 20, offset_param integer DEFAULT 0) RETURNS TABLE(event_id uuid, recipe_id uuid, recipe_title character varying, recipe_image_url text, difficulty character varying, rating numeric, cooking_image_url text, duration_minutes integer, cooked_at timestamp with time zone, times_cooked bigint)
    LANGUAGE plpgsql STABLE SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        rce.id as event_id,
        rce.recipe_id,
        r.title as recipe_title,
        r.image_url as recipe_image_url,
        r.difficulty,
        rce.rating,
        rce.image_url as cooking_image_url,
        rce.duration_minutes,
        rce.cooked_at,
        (
            SELECT COUNT(*)
            FROM recipe_cooking_events rce2
            WHERE rce2.recipe_id = rce.recipe_id
            AND rce2.user_id = user_id_param
        ) as times_cooked
    FROM recipe_cooking_events rce
    INNER JOIN recipes r ON r.id = rce.recipe_id
    WHERE
        rce.user_id = user_id_param
        AND rce.cooked_at >= NOW() - INTERVAL '1 day' * time_window_days
    ORDER BY rce.cooked_at DESC
    LIMIT limit_param
    OFFSET offset_param;
END;
$$;


--
-- Name: FUNCTION get_user_cooking_history(user_id_param uuid, time_window_days integer, limit_param integer, offset_param integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.get_user_cooking_history(user_id_param uuid, time_window_days integer, limit_param integer, offset_param integer) IS 'Returns individual cooking events for a user with recipe details and per-event data (rating, photo, duration). Each row is a single cooking session.';


--
-- Name: is_user_anonymous(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.is_user_anonymous(user_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    is_anon BOOLEAN;
BEGIN
    SELECT is_anonymous INTO is_anon
    FROM auth.users
    WHERE id = user_id;

    RETURN COALESCE(is_anon, false);
END;
$$;


--
-- Name: FUNCTION is_user_anonymous(user_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.is_user_anonymous(user_id uuid) IS 'Returns true if the user is anonymous, false otherwise';


--
-- Name: migrate_instruction(jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.migrate_instruction(instruction jsonb) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    text_content TEXT;
    new_instruction JSONB;
BEGIN
    -- Check if instruction already has 'title' field (already migrated)
    IF instruction ? 'title' THEN
        RETURN instruction;
    END IF;

    -- Check if instruction has 'text' field (old format)
    IF NOT instruction ? 'text' THEN
        RETURN instruction;
    END IF;

    -- Extract the text content
    text_content := instruction->>'text';

    -- Migration strategy: use "Title" as title, move text to description
    new_instruction := jsonb_build_object(
        'step_number', instruction->'step_number',
        'title', 'Title',
        'description', text_content,
        'timer_minutes', instruction->'timer_minutes',
        'group', instruction->'group'
    );

    RETURN new_instruction;
END;
$$;


--
-- Name: FUNCTION migrate_instruction(instruction jsonb); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.migrate_instruction(instruction jsonb) IS 'Migrates a single instruction from old format (with "text") to new format (with "title" and "description")';


--
-- Name: migrate_instructions_array(jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.migrate_instructions_array(instructions jsonb) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    result JSONB := '[]'::jsonb;
    instruction JSONB;
BEGIN
    -- If instructions is not an array, return it as-is
    IF jsonb_typeof(instructions) != 'array' THEN
        RETURN instructions;
    END IF;

    -- Iterate through each instruction and migrate it
    FOR instruction IN SELECT * FROM jsonb_array_elements(instructions)
    LOOP
        result := result || jsonb_build_array(migrate_instruction(instruction));
    END LOOP;

    RETURN result;
END;
$$;


--
-- Name: FUNCTION migrate_instructions_array(instructions jsonb); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.migrate_instructions_array(instructions jsonb) IS 'Migrates an array of instructions from old format to new format';


--
-- Name: recipes_search_vector_update(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.recipes_search_vector_update() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  ingredients_text text;
  instructions_text text;
  lang_config regconfig;
BEGIN
  -- Extract text from JSONB ingredients array
  SELECT string_agg(item->>'name', ' ')
  INTO ingredients_text
  FROM jsonb_array_elements(NEW.ingredients) AS item;

  -- Extract text from JSONB instructions array
  SELECT string_agg(item->>'text', ' ')
  INTO instructions_text
  FROM jsonb_array_elements(NEW.instructions) AS item;

  -- Select language-specific dictionary for better stemming and stop word removal
  lang_config := CASE
    WHEN NEW.language = 'fr' THEN 'french'::regconfig
    WHEN NEW.language = 'en' THEN 'english'::regconfig
    ELSE 'simple'::regconfig
  END;

  -- Build the search vector with weighted components
  NEW.search_vector :=
    setweight(to_tsvector(lang_config, coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector(lang_config, coalesce(array_to_string(NEW.tags, ' '), '')), 'B') ||
    setweight(to_tsvector(lang_config, coalesce(array_to_string(NEW.categories, ' '), '')), 'B') ||
    setweight(to_tsvector(lang_config, coalesce(NEW.description, '')), 'C') ||
    setweight(to_tsvector(lang_config, coalesce(ingredients_text, '')), 'D') ||
    setweight(to_tsvector(lang_config, coalesce(instructions_text, '')), 'D');

  RETURN NEW;
END;
$$;


--
-- Name: FUNCTION recipes_search_vector_update(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.recipes_search_vector_update() IS 'Trigger function for language-aware search vector updates';


--
-- Name: search_recipes_full_text(text, uuid, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_recipes_full_text(search_query text, user_id_param uuid DEFAULT NULL::uuid, limit_param integer DEFAULT 20, offset_param integer DEFAULT 0) RETURNS TABLE(id uuid, title character varying, description text, image_url text, servings integer, difficulty character varying, tags text[], categories text[], prep_time_minutes integer, cook_time_minutes integer, total_time_minutes integer, created_by uuid, is_public boolean, fork_count integer, average_rating numeric, rating_count integer, total_times_cooked integer, created_at timestamp with time zone, rank real)
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
  query_tsquery tsquery;
BEGIN
  -- Pre-compile the tsquery once for better performance
  query_tsquery := plainto_tsquery('simple', search_query);

  RETURN QUERY
  SELECT
    r.id,
    r.title,
    r.description,
    r.image_url,
    r.servings,
    r.difficulty,
    r.tags,
    r.categories,
    r.prep_time_minutes,
    r.cook_time_minutes,
    r.total_time_minutes,
    r.created_by,
    r.is_public,
    r.fork_count,
    r.average_rating,
    r.rating_count,
    r.total_times_cooked,
    r.created_at,
    -- Use ts_rank_cd for better ranking with normalization
    ts_rank_cd(r.search_vector, query_tsquery, 32) as rank
  FROM recipes r
  WHERE
    -- Use GIN index for fast search
    r.search_vector @@ query_tsquery
    AND (
      -- Use index for public/user filtering
      r.is_public = true
      OR (user_id_param IS NOT NULL AND r.created_by = user_id_param)
    )
  ORDER BY rank DESC, r.created_at DESC
  LIMIT limit_param
  OFFSET offset_param;
END;
$$;


--
-- Name: FUNCTION search_recipes_full_text(search_query text, user_id_param uuid, limit_param integer, offset_param integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.search_recipes_full_text(search_query text, user_id_param uuid, limit_param integer, offset_param integer) IS 'Full-text search function for recipes with ranking and aggregated metrics (ratings, cooked count). Returns recipes sorted by relevance.';


--
-- Name: update_recipe_cooked_count(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_recipe_cooked_count() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
DECLARE
  cooked_delta INTEGER;
BEGIN
  -- Calculate the change in times_cooked
  IF TG_OP = 'INSERT' THEN
    -- New user_recipe_data record created
    cooked_delta := COALESCE(NEW.times_cooked, 0);
  ELSIF TG_OP = 'UPDATE' THEN
    -- Existing record updated
    cooked_delta := COALESCE(NEW.times_cooked, 0) - COALESCE(OLD.times_cooked, 0);
  ELSIF TG_OP = 'DELETE' THEN
    -- Record deleted (edge case)
    cooked_delta := -COALESCE(OLD.times_cooked, 0);
  END IF;

  -- Only update if there's an actual change
  IF cooked_delta != 0 THEN
    UPDATE public.recipes
    SET total_times_cooked = GREATEST(total_times_cooked + cooked_delta, 0)
    WHERE id = COALESCE(NEW.recipe_id, OLD.recipe_id);
  END IF;

  RETURN NEW;
END;
$$;


--
-- Name: FUNCTION update_recipe_cooked_count(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.update_recipe_cooked_count() IS 'Trigger function that automatically updates recipes.total_times_cooked when user_recipe_data.times_cooked changes. Handles INSERT, UPDATE, and DELETE operations.';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: validate_instruction_format(jsonb); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.validate_instruction_format(instruction jsonb) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    -- An instruction must have step_number, title, and description
    RETURN (
        instruction ? 'step_number' AND
        instruction ? 'title' AND
        instruction ? 'description'
    );
END;
$$;


--
-- Name: FUNCTION validate_instruction_format(instruction jsonb); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.validate_instruction_format(instruction jsonb) IS 'Validates that an instruction has the required fields: step_number, title, and description';


--
-- Name: apply_rls(jsonb, integer); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.apply_rls(wal jsonb, max_record_bytes integer DEFAULT (1024 * 1024)) RETURNS SETOF realtime.wal_rls
    LANGUAGE plpgsql
    AS $$
declare
-- Regclass of the table e.g. public.notes
entity_ regclass = (quote_ident(wal ->> 'schema') || '.' || quote_ident(wal ->> 'table'))::regclass;

-- I, U, D, T: insert, update ...
action realtime.action = (
    case wal ->> 'action'
        when 'I' then 'INSERT'
        when 'U' then 'UPDATE'
        when 'D' then 'DELETE'
        else 'ERROR'
    end
);

-- Is row level security enabled for the table
is_rls_enabled bool = relrowsecurity from pg_class where oid = entity_;

subscriptions realtime.subscription[] = array_agg(subs)
    from
        realtime.subscription subs
    where
        subs.entity = entity_;

-- Subscription vars
roles regrole[] = array_agg(distinct us.claims_role::text)
    from
        unnest(subscriptions) us;

working_role regrole;
claimed_role regrole;
claims jsonb;

subscription_id uuid;
subscription_has_access bool;
visible_to_subscription_ids uuid[] = '{}';

-- structured info for wal's columns
columns realtime.wal_column[];
-- previous identity values for update/delete
old_columns realtime.wal_column[];

error_record_exceeds_max_size boolean = octet_length(wal::text) > max_record_bytes;

-- Primary jsonb output for record
output jsonb;

begin
perform set_config('role', null, true);

columns =
    array_agg(
        (
            x->>'name',
            x->>'type',
            x->>'typeoid',
            realtime.cast(
                (x->'value') #>> '{}',
                coalesce(
                    (x->>'typeoid')::regtype, -- null when wal2json version <= 2.4
                    (x->>'type')::regtype
                )
            ),
            (pks ->> 'name') is not null,
            true
        )::realtime.wal_column
    )
    from
        jsonb_array_elements(wal -> 'columns') x
        left join jsonb_array_elements(wal -> 'pk') pks
            on (x ->> 'name') = (pks ->> 'name');

old_columns =
    array_agg(
        (
            x->>'name',
            x->>'type',
            x->>'typeoid',
            realtime.cast(
                (x->'value') #>> '{}',
                coalesce(
                    (x->>'typeoid')::regtype, -- null when wal2json version <= 2.4
                    (x->>'type')::regtype
                )
            ),
            (pks ->> 'name') is not null,
            true
        )::realtime.wal_column
    )
    from
        jsonb_array_elements(wal -> 'identity') x
        left join jsonb_array_elements(wal -> 'pk') pks
            on (x ->> 'name') = (pks ->> 'name');

for working_role in select * from unnest(roles) loop

    -- Update `is_selectable` for columns and old_columns
    columns =
        array_agg(
            (
                c.name,
                c.type_name,
                c.type_oid,
                c.value,
                c.is_pkey,
                pg_catalog.has_column_privilege(working_role, entity_, c.name, 'SELECT')
            )::realtime.wal_column
        )
        from
            unnest(columns) c;

    old_columns =
            array_agg(
                (
                    c.name,
                    c.type_name,
                    c.type_oid,
                    c.value,
                    c.is_pkey,
                    pg_catalog.has_column_privilege(working_role, entity_, c.name, 'SELECT')
                )::realtime.wal_column
            )
            from
                unnest(old_columns) c;

    if action <> 'DELETE' and count(1) = 0 from unnest(columns) c where c.is_pkey then
        return next (
            jsonb_build_object(
                'schema', wal ->> 'schema',
                'table', wal ->> 'table',
                'type', action
            ),
            is_rls_enabled,
            -- subscriptions is already filtered by entity
            (select array_agg(s.subscription_id) from unnest(subscriptions) as s where claims_role = working_role),
            array['Error 400: Bad Request, no primary key']
        )::realtime.wal_rls;

    -- The claims role does not have SELECT permission to the primary key of entity
    elsif action <> 'DELETE' and sum(c.is_selectable::int) <> count(1) from unnest(columns) c where c.is_pkey then
        return next (
            jsonb_build_object(
                'schema', wal ->> 'schema',
                'table', wal ->> 'table',
                'type', action
            ),
            is_rls_enabled,
            (select array_agg(s.subscription_id) from unnest(subscriptions) as s where claims_role = working_role),
            array['Error 401: Unauthorized']
        )::realtime.wal_rls;

    else
        output = jsonb_build_object(
            'schema', wal ->> 'schema',
            'table', wal ->> 'table',
            'type', action,
            'commit_timestamp', to_char(
                ((wal ->> 'timestamp')::timestamptz at time zone 'utc'),
                'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
            ),
            'columns', (
                select
                    jsonb_agg(
                        jsonb_build_object(
                            'name', pa.attname,
                            'type', pt.typname
                        )
                        order by pa.attnum asc
                    )
                from
                    pg_attribute pa
                    join pg_type pt
                        on pa.atttypid = pt.oid
                where
                    attrelid = entity_
                    and attnum > 0
                    and pg_catalog.has_column_privilege(working_role, entity_, pa.attname, 'SELECT')
            )
        )
        -- Add "record" key for insert and update
        || case
            when action in ('INSERT', 'UPDATE') then
                jsonb_build_object(
                    'record',
                    (
                        select
                            jsonb_object_agg(
                                -- if unchanged toast, get column name and value from old record
                                coalesce((c).name, (oc).name),
                                case
                                    when (c).name is null then (oc).value
                                    else (c).value
                                end
                            )
                        from
                            unnest(columns) c
                            full outer join unnest(old_columns) oc
                                on (c).name = (oc).name
                        where
                            coalesce((c).is_selectable, (oc).is_selectable)
                            and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                    )
                )
            else '{}'::jsonb
        end
        -- Add "old_record" key for update and delete
        || case
            when action = 'UPDATE' then
                jsonb_build_object(
                        'old_record',
                        (
                            select jsonb_object_agg((c).name, (c).value)
                            from unnest(old_columns) c
                            where
                                (c).is_selectable
                                and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                        )
                    )
            when action = 'DELETE' then
                jsonb_build_object(
                    'old_record',
                    (
                        select jsonb_object_agg((c).name, (c).value)
                        from unnest(old_columns) c
                        where
                            (c).is_selectable
                            and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                            and ( not is_rls_enabled or (c).is_pkey ) -- if RLS enabled, we can't secure deletes so filter to pkey
                    )
                )
            else '{}'::jsonb
        end;

        -- Create the prepared statement
        if is_rls_enabled and action <> 'DELETE' then
            if (select 1 from pg_prepared_statements where name = 'walrus_rls_stmt' limit 1) > 0 then
                deallocate walrus_rls_stmt;
            end if;
            execute realtime.build_prepared_statement_sql('walrus_rls_stmt', entity_, columns);
        end if;

        visible_to_subscription_ids = '{}';

        for subscription_id, claims in (
                select
                    subs.subscription_id,
                    subs.claims
                from
                    unnest(subscriptions) subs
                where
                    subs.entity = entity_
                    and subs.claims_role = working_role
                    and (
                        realtime.is_visible_through_filters(columns, subs.filters)
                        or (
                          action = 'DELETE'
                          and realtime.is_visible_through_filters(old_columns, subs.filters)
                        )
                    )
        ) loop

            if not is_rls_enabled or action = 'DELETE' then
                visible_to_subscription_ids = visible_to_subscription_ids || subscription_id;
            else
                -- Check if RLS allows the role to see the record
                perform
                    -- Trim leading and trailing quotes from working_role because set_config
                    -- doesn't recognize the role as valid if they are included
                    set_config('role', trim(both '"' from working_role::text), true),
                    set_config('request.jwt.claims', claims::text, true);

                execute 'execute walrus_rls_stmt' into subscription_has_access;

                if subscription_has_access then
                    visible_to_subscription_ids = visible_to_subscription_ids || subscription_id;
                end if;
            end if;
        end loop;

        perform set_config('role', null, true);

        return next (
            output,
            is_rls_enabled,
            visible_to_subscription_ids,
            case
                when error_record_exceeds_max_size then array['Error 413: Payload Too Large']
                else '{}'
            end
        )::realtime.wal_rls;

    end if;
end loop;

perform set_config('role', null, true);
end;
$$;


--
-- Name: broadcast_changes(text, text, text, text, text, record, record, text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.broadcast_changes(topic_name text, event_name text, operation text, table_name text, table_schema text, new record, old record, level text DEFAULT 'ROW'::text) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    -- Declare a variable to hold the JSONB representation of the row
    row_data jsonb := '{}'::jsonb;
BEGIN
    IF level = 'STATEMENT' THEN
        RAISE EXCEPTION 'function can only be triggered for each row, not for each statement';
    END IF;
    -- Check the operation type and handle accordingly
    IF operation = 'INSERT' OR operation = 'UPDATE' OR operation = 'DELETE' THEN
        row_data := jsonb_build_object('old_record', OLD, 'record', NEW, 'operation', operation, 'table', table_name, 'schema', table_schema);
        PERFORM realtime.send (row_data, event_name, topic_name);
    ELSE
        RAISE EXCEPTION 'Unexpected operation type: %', operation;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to process the row: %', SQLERRM;
END;

$$;


--
-- Name: build_prepared_statement_sql(text, regclass, realtime.wal_column[]); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.build_prepared_statement_sql(prepared_statement_name text, entity regclass, columns realtime.wal_column[]) RETURNS text
    LANGUAGE sql
    AS $$
      /*
      Builds a sql string that, if executed, creates a prepared statement to
      tests retrive a row from *entity* by its primary key columns.
      Example
          select realtime.build_prepared_statement_sql('public.notes', '{"id"}'::text[], '{"bigint"}'::text[])
      */
          select
      'prepare ' || prepared_statement_name || ' as
          select
              exists(
                  select
                      1
                  from
                      ' || entity || '
                  where
                      ' || string_agg(quote_ident(pkc.name) || '=' || quote_nullable(pkc.value #>> '{}') , ' and ') || '
              )'
          from
              unnest(columns) pkc
          where
              pkc.is_pkey
          group by
              entity
      $$;


--
-- Name: cast(text, regtype); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime."cast"(val text, type_ regtype) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
    declare
      res jsonb;
    begin
      execute format('select to_jsonb(%L::'|| type_::text || ')', val)  into res;
      return res;
    end
    $$;


--
-- Name: check_equality_op(realtime.equality_op, regtype, text, text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.check_equality_op(op realtime.equality_op, type_ regtype, val_1 text, val_2 text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
      /*
      Casts *val_1* and *val_2* as type *type_* and check the *op* condition for truthiness
      */
      declare
          op_symbol text = (
              case
                  when op = 'eq' then '='
                  when op = 'neq' then '!='
                  when op = 'lt' then '<'
                  when op = 'lte' then '<='
                  when op = 'gt' then '>'
                  when op = 'gte' then '>='
                  when op = 'in' then '= any'
                  else 'UNKNOWN OP'
              end
          );
          res boolean;
      begin
          execute format(
              'select %L::'|| type_::text || ' ' || op_symbol
              || ' ( %L::'
              || (
                  case
                      when op = 'in' then type_::text || '[]'
                      else type_::text end
              )
              || ')', val_1, val_2) into res;
          return res;
      end;
      $$;


--
-- Name: is_visible_through_filters(realtime.wal_column[], realtime.user_defined_filter[]); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.is_visible_through_filters(columns realtime.wal_column[], filters realtime.user_defined_filter[]) RETURNS boolean
    LANGUAGE sql IMMUTABLE
    AS $_$
    /*
    Should the record be visible (true) or filtered out (false) after *filters* are applied
    */
        select
            -- Default to allowed when no filters present
            $2 is null -- no filters. this should not happen because subscriptions has a default
            or array_length($2, 1) is null -- array length of an empty array is null
            or bool_and(
                coalesce(
                    realtime.check_equality_op(
                        op:=f.op,
                        type_:=coalesce(
                            col.type_oid::regtype, -- null when wal2json version <= 2.4
                            col.type_name::regtype
                        ),
                        -- cast jsonb to text
                        val_1:=col.value #>> '{}',
                        val_2:=f.value
                    ),
                    false -- if null, filter does not match
                )
            )
        from
            unnest(filters) f
            join unnest(columns) col
                on f.column_name = col.name;
    $_$;


--
-- Name: list_changes(name, name, integer, integer); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.list_changes(publication name, slot_name name, max_changes integer, max_record_bytes integer) RETURNS SETOF realtime.wal_rls
    LANGUAGE sql
    SET log_min_messages TO 'fatal'
    AS $$
      with pub as (
        select
          concat_ws(
            ',',
            case when bool_or(pubinsert) then 'insert' else null end,
            case when bool_or(pubupdate) then 'update' else null end,
            case when bool_or(pubdelete) then 'delete' else null end
          ) as w2j_actions,
          coalesce(
            string_agg(
              realtime.quote_wal2json(format('%I.%I', schemaname, tablename)::regclass),
              ','
            ) filter (where ppt.tablename is not null and ppt.tablename not like '% %'),
            ''
          ) w2j_add_tables
        from
          pg_publication pp
          left join pg_publication_tables ppt
            on pp.pubname = ppt.pubname
        where
          pp.pubname = publication
        group by
          pp.pubname
        limit 1
      ),
      w2j as (
        select
          x.*, pub.w2j_add_tables
        from
          pub,
          pg_logical_slot_get_changes(
            slot_name, null, max_changes,
            'include-pk', 'true',
            'include-transaction', 'false',
            'include-timestamp', 'true',
            'include-type-oids', 'true',
            'format-version', '2',
            'actions', pub.w2j_actions,
            'add-tables', pub.w2j_add_tables
          ) x
      )
      select
        xyz.wal,
        xyz.is_rls_enabled,
        xyz.subscription_ids,
        xyz.errors
      from
        w2j,
        realtime.apply_rls(
          wal := w2j.data::jsonb,
          max_record_bytes := max_record_bytes
        ) xyz(wal, is_rls_enabled, subscription_ids, errors)
      where
        w2j.w2j_add_tables <> ''
        and xyz.subscription_ids[1] is not null
    $$;


--
-- Name: quote_wal2json(regclass); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.quote_wal2json(entity regclass) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
      select
        (
          select string_agg('' || ch,'')
          from unnest(string_to_array(nsp.nspname::text, null)) with ordinality x(ch, idx)
          where
            not (x.idx = 1 and x.ch = '"')
            and not (
              x.idx = array_length(string_to_array(nsp.nspname::text, null), 1)
              and x.ch = '"'
            )
        )
        || '.'
        || (
          select string_agg('' || ch,'')
          from unnest(string_to_array(pc.relname::text, null)) with ordinality x(ch, idx)
          where
            not (x.idx = 1 and x.ch = '"')
            and not (
              x.idx = array_length(string_to_array(nsp.nspname::text, null), 1)
              and x.ch = '"'
            )
          )
      from
        pg_class pc
        join pg_namespace nsp
          on pc.relnamespace = nsp.oid
      where
        pc.oid = entity
    $$;


--
-- Name: send(jsonb, text, text, boolean); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.send(payload jsonb, event text, topic text, private boolean DEFAULT true) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  generated_id uuid;
  final_payload jsonb;
BEGIN
  BEGIN
    -- Generate a new UUID for the id
    generated_id := gen_random_uuid();

    -- Check if payload has an 'id' key, if not, add the generated UUID
    IF payload ? 'id' THEN
      final_payload := payload;
    ELSE
      final_payload := jsonb_set(payload, '{id}', to_jsonb(generated_id));
    END IF;

    -- Set the topic configuration
    EXECUTE format('SET LOCAL realtime.topic TO %L', topic);

    -- Attempt to insert the message
    INSERT INTO realtime.messages (id, payload, event, topic, private, extension)
    VALUES (generated_id, final_payload, event, topic, private, 'broadcast');
  EXCEPTION
    WHEN OTHERS THEN
      -- Capture and notify the error
      RAISE WARNING 'ErrorSendingBroadcastMessage: %', SQLERRM;
  END;
END;
$$;


--
-- Name: subscription_check_filters(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.subscription_check_filters() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    /*
    Validates that the user defined filters for a subscription:
    - refer to valid columns that the claimed role may access
    - values are coercable to the correct column type
    */
    declare
        col_names text[] = coalesce(
                array_agg(c.column_name order by c.ordinal_position),
                '{}'::text[]
            )
            from
                information_schema.columns c
            where
                format('%I.%I', c.table_schema, c.table_name)::regclass = new.entity
                and pg_catalog.has_column_privilege(
                    (new.claims ->> 'role'),
                    format('%I.%I', c.table_schema, c.table_name)::regclass,
                    c.column_name,
                    'SELECT'
                );
        filter realtime.user_defined_filter;
        col_type regtype;

        in_val jsonb;
    begin
        for filter in select * from unnest(new.filters) loop
            -- Filtered column is valid
            if not filter.column_name = any(col_names) then
                raise exception 'invalid column for filter %', filter.column_name;
            end if;

            -- Type is sanitized and safe for string interpolation
            col_type = (
                select atttypid::regtype
                from pg_catalog.pg_attribute
                where attrelid = new.entity
                      and attname = filter.column_name
            );
            if col_type is null then
                raise exception 'failed to lookup type for column %', filter.column_name;
            end if;

            -- Set maximum number of entries for in filter
            if filter.op = 'in'::realtime.equality_op then
                in_val = realtime.cast(filter.value, (col_type::text || '[]')::regtype);
                if coalesce(jsonb_array_length(in_val), 0) > 100 then
                    raise exception 'too many values for `in` filter. Maximum 100';
                end if;
            else
                -- raises an exception if value is not coercable to type
                perform realtime.cast(filter.value, col_type);
            end if;

        end loop;

        -- Apply consistent order to filters so the unique constraint on
        -- (subscription_id, entity, filters) can't be tricked by a different filter order
        new.filters = coalesce(
            array_agg(f order by f.column_name, f.op, f.value),
            '{}'
        ) from unnest(new.filters) f;

        return new;
    end;
    $$;


--
-- Name: to_regrole(text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.to_regrole(role_name text) RETURNS regrole
    LANGUAGE sql IMMUTABLE
    AS $$ select role_name::regrole $$;


--
-- Name: topic(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.topic() RETURNS text
    LANGUAGE sql STABLE
    AS $$
select nullif(current_setting('realtime.topic', true), '')::text;
$$;


--
-- Name: add_prefixes(text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.add_prefixes(_bucket_id text, _name text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    prefixes text[];
BEGIN
    prefixes := "storage"."get_prefixes"("_name");

    IF array_length(prefixes, 1) > 0 THEN
        INSERT INTO storage.prefixes (name, bucket_id)
        SELECT UNNEST(prefixes) as name, "_bucket_id" ON CONFLICT DO NOTHING;
    END IF;
END;
$$;


--
-- Name: can_insert_object(text, text, uuid, jsonb); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  INSERT INTO "storage"."objects" ("bucket_id", "name", "owner", "metadata") VALUES (bucketid, name, owner, metadata);
  -- hack to rollback the successful insert
  RAISE sqlstate 'PT200' using
  message = 'ROLLBACK',
  detail = 'rollback successful insert';
END
$$;


--
-- Name: delete_leaf_prefixes(text[], text[]); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.delete_leaf_prefixes(bucket_ids text[], names text[]) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_rows_deleted integer;
BEGIN
    LOOP
        WITH candidates AS (
            SELECT DISTINCT
                t.bucket_id,
                unnest(storage.get_prefixes(t.name)) AS name
            FROM unnest(bucket_ids, names) AS t(bucket_id, name)
        ),
        uniq AS (
             SELECT
                 bucket_id,
                 name,
                 storage.get_level(name) AS level
             FROM candidates
             WHERE name <> ''
             GROUP BY bucket_id, name
        ),
        leaf AS (
             SELECT
                 p.bucket_id,
                 p.name,
                 p.level
             FROM storage.prefixes AS p
                  JOIN uniq AS u
                       ON u.bucket_id = p.bucket_id
                           AND u.name = p.name
                           AND u.level = p.level
             WHERE NOT EXISTS (
                 SELECT 1
                 FROM storage.objects AS o
                 WHERE o.bucket_id = p.bucket_id
                   AND o.level = p.level + 1
                   AND o.name COLLATE "C" LIKE p.name || '/%'
             )
             AND NOT EXISTS (
                 SELECT 1
                 FROM storage.prefixes AS c
                 WHERE c.bucket_id = p.bucket_id
                   AND c.level = p.level + 1
                   AND c.name COLLATE "C" LIKE p.name || '/%'
             )
        )
        DELETE
        FROM storage.prefixes AS p
            USING leaf AS l
        WHERE p.bucket_id = l.bucket_id
          AND p.name = l.name
          AND p.level = l.level;

        GET DIAGNOSTICS v_rows_deleted = ROW_COUNT;
        EXIT WHEN v_rows_deleted = 0;
    END LOOP;
END;
$$;


--
-- Name: delete_prefix(text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.delete_prefix(_bucket_id text, _name text) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    -- Check if we can delete the prefix
    IF EXISTS(
        SELECT FROM "storage"."prefixes"
        WHERE "prefixes"."bucket_id" = "_bucket_id"
          AND level = "storage"."get_level"("_name") + 1
          AND "prefixes"."name" COLLATE "C" LIKE "_name" || '/%'
        LIMIT 1
    )
    OR EXISTS(
        SELECT FROM "storage"."objects"
        WHERE "objects"."bucket_id" = "_bucket_id"
          AND "storage"."get_level"("objects"."name") = "storage"."get_level"("_name") + 1
          AND "objects"."name" COLLATE "C" LIKE "_name" || '/%'
        LIMIT 1
    ) THEN
    -- There are sub-objects, skip deletion
    RETURN false;
    ELSE
        DELETE FROM "storage"."prefixes"
        WHERE "prefixes"."bucket_id" = "_bucket_id"
          AND level = "storage"."get_level"("_name")
          AND "prefixes"."name" = "_name";
        RETURN true;
    END IF;
END;
$$;


--
-- Name: delete_prefix_hierarchy_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.delete_prefix_hierarchy_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    prefix text;
BEGIN
    prefix := "storage"."get_prefix"(OLD."name");

    IF coalesce(prefix, '') != '' THEN
        PERFORM "storage"."delete_prefix"(OLD."bucket_id", prefix);
    END IF;

    RETURN OLD;
END;
$$;


--
-- Name: enforce_bucket_name_length(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.enforce_bucket_name_length() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    if length(new.name) > 100 then
        raise exception 'bucket name "%" is too long (% characters). Max is 100.', new.name, length(new.name);
    end if;
    return new;
end;
$$;


--
-- Name: extension(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.extension(name text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
    _filename text;
BEGIN
    SELECT string_to_array(name, '/') INTO _parts;
    SELECT _parts[array_length(_parts,1)] INTO _filename;
    RETURN reverse(split_part(reverse(_filename), '.', 1));
END
$$;


--
-- Name: filename(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.filename(name text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[array_length(_parts,1)];
END
$$;


--
-- Name: foldername(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.foldername(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
BEGIN
    -- Split on "/" to get path segments
    SELECT string_to_array(name, '/') INTO _parts;
    -- Return everything except the last segment
    RETURN _parts[1 : array_length(_parts,1) - 1];
END
$$;


--
-- Name: get_level(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_level(name text) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
SELECT array_length(string_to_array("name", '/'), 1);
$$;


--
-- Name: get_prefix(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_prefix(name text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
SELECT
    CASE WHEN strpos("name", '/') > 0 THEN
             regexp_replace("name", '[\/]{1}[^\/]+\/?$', '')
         ELSE
             ''
        END;
$_$;


--
-- Name: get_prefixes(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_prefixes(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE STRICT
    AS $$
DECLARE
    parts text[];
    prefixes text[];
    prefix text;
BEGIN
    -- Split the name into parts by '/'
    parts := string_to_array("name", '/');
    prefixes := '{}';

    -- Construct the prefixes, stopping one level below the last part
    FOR i IN 1..array_length(parts, 1) - 1 LOOP
            prefix := array_to_string(parts[1:i], '/');
            prefixes := array_append(prefixes, prefix);
    END LOOP;

    RETURN prefixes;
END;
$$;


--
-- Name: get_size_by_bucket(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_size_by_bucket() RETURNS TABLE(size bigint, bucket_id text)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    return query
        select sum((metadata->>'size')::bigint) as size, obj.bucket_id
        from "storage".objects as obj
        group by obj.bucket_id;
END
$$;


--
-- Name: list_multipart_uploads_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, next_key_token text DEFAULT ''::text, next_upload_token text DEFAULT ''::text) RETURNS TABLE(key text, id text, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(key COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                        substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1)))
                    ELSE
                        key
                END AS key, id, created_at
            FROM
                storage.s3_multipart_uploads
            WHERE
                bucket_id = $5 AND
                key ILIKE $1 || ''%'' AND
                CASE
                    WHEN $4 != '''' AND $6 = '''' THEN
                        CASE
                            WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                                substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                key COLLATE "C" > $4
                            END
                    ELSE
                        true
                END AND
                CASE
                    WHEN $6 != '''' THEN
                        id COLLATE "C" > $6
                    ELSE
                        true
                    END
            ORDER BY
                key COLLATE "C" ASC, created_at ASC) as e order by key COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_key_token, bucket_id, next_upload_token;
END;
$_$;


--
-- Name: list_objects_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, start_after text DEFAULT ''::text, next_token text DEFAULT ''::text) RETURNS TABLE(name text, id uuid, metadata jsonb, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(name COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(name from length($1) + 1)) > 0 THEN
                        substring(name from 1 for length($1) + position($2 IN substring(name from length($1) + 1)))
                    ELSE
                        name
                END AS name, id, metadata, updated_at
            FROM
                storage.objects
            WHERE
                bucket_id = $5 AND
                name ILIKE $1 || ''%'' AND
                CASE
                    WHEN $6 != '''' THEN
                    name COLLATE "C" > $6
                ELSE true END
                AND CASE
                    WHEN $4 != '''' THEN
                        CASE
                            WHEN position($2 IN substring(name from length($1) + 1)) > 0 THEN
                                substring(name from 1 for length($1) + position($2 IN substring(name from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                name COLLATE "C" > $4
                            END
                    ELSE
                        true
                END
            ORDER BY
                name COLLATE "C" ASC) as e order by name COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_token, bucket_id, start_after;
END;
$_$;


--
-- Name: lock_top_prefixes(text[], text[]); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.lock_top_prefixes(bucket_ids text[], names text[]) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_bucket text;
    v_top text;
BEGIN
    FOR v_bucket, v_top IN
        SELECT DISTINCT t.bucket_id,
            split_part(t.name, '/', 1) AS top
        FROM unnest(bucket_ids, names) AS t(bucket_id, name)
        WHERE t.name <> ''
        ORDER BY 1, 2
        LOOP
            PERFORM pg_advisory_xact_lock(hashtextextended(v_bucket || '/' || v_top, 0));
        END LOOP;
END;
$$;


--
-- Name: objects_delete_cleanup(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_delete_cleanup() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_bucket_ids text[];
    v_names      text[];
BEGIN
    IF current_setting('storage.gc.prefixes', true) = '1' THEN
        RETURN NULL;
    END IF;

    PERFORM set_config('storage.gc.prefixes', '1', true);

    SELECT COALESCE(array_agg(d.bucket_id), '{}'),
           COALESCE(array_agg(d.name), '{}')
    INTO v_bucket_ids, v_names
    FROM deleted AS d
    WHERE d.name <> '';

    PERFORM storage.lock_top_prefixes(v_bucket_ids, v_names);
    PERFORM storage.delete_leaf_prefixes(v_bucket_ids, v_names);

    RETURN NULL;
END;
$$;


--
-- Name: objects_insert_prefix_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_insert_prefix_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    NEW.level := "storage"."get_level"(NEW."name");

    RETURN NEW;
END;
$$;


--
-- Name: objects_update_cleanup(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_update_cleanup() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    -- NEW - OLD (destinations to create prefixes for)
    v_add_bucket_ids text[];
    v_add_names      text[];

    -- OLD - NEW (sources to prune)
    v_src_bucket_ids text[];
    v_src_names      text[];
BEGIN
    IF TG_OP <> 'UPDATE' THEN
        RETURN NULL;
    END IF;

    -- 1) Compute NEW−OLD (added paths) and OLD−NEW (moved-away paths)
    WITH added AS (
        SELECT n.bucket_id, n.name
        FROM new_rows n
        WHERE n.name <> '' AND position('/' in n.name) > 0
        EXCEPT
        SELECT o.bucket_id, o.name FROM old_rows o WHERE o.name <> ''
    ),
    moved AS (
         SELECT o.bucket_id, o.name
         FROM old_rows o
         WHERE o.name <> ''
         EXCEPT
         SELECT n.bucket_id, n.name FROM new_rows n WHERE n.name <> ''
    )
    SELECT
        -- arrays for ADDED (dest) in stable order
        COALESCE( (SELECT array_agg(a.bucket_id ORDER BY a.bucket_id, a.name) FROM added a), '{}' ),
        COALESCE( (SELECT array_agg(a.name      ORDER BY a.bucket_id, a.name) FROM added a), '{}' ),
        -- arrays for MOVED (src) in stable order
        COALESCE( (SELECT array_agg(m.bucket_id ORDER BY m.bucket_id, m.name) FROM moved m), '{}' ),
        COALESCE( (SELECT array_agg(m.name      ORDER BY m.bucket_id, m.name) FROM moved m), '{}' )
    INTO v_add_bucket_ids, v_add_names, v_src_bucket_ids, v_src_names;

    -- Nothing to do?
    IF (array_length(v_add_bucket_ids, 1) IS NULL) AND (array_length(v_src_bucket_ids, 1) IS NULL) THEN
        RETURN NULL;
    END IF;

    -- 2) Take per-(bucket, top) locks: ALL prefixes in consistent global order to prevent deadlocks
    DECLARE
        v_all_bucket_ids text[];
        v_all_names text[];
    BEGIN
        -- Combine source and destination arrays for consistent lock ordering
        v_all_bucket_ids := COALESCE(v_src_bucket_ids, '{}') || COALESCE(v_add_bucket_ids, '{}');
        v_all_names := COALESCE(v_src_names, '{}') || COALESCE(v_add_names, '{}');

        -- Single lock call ensures consistent global ordering across all transactions
        IF array_length(v_all_bucket_ids, 1) IS NOT NULL THEN
            PERFORM storage.lock_top_prefixes(v_all_bucket_ids, v_all_names);
        END IF;
    END;

    -- 3) Create destination prefixes (NEW−OLD) BEFORE pruning sources
    IF array_length(v_add_bucket_ids, 1) IS NOT NULL THEN
        WITH candidates AS (
            SELECT DISTINCT t.bucket_id, unnest(storage.get_prefixes(t.name)) AS name
            FROM unnest(v_add_bucket_ids, v_add_names) AS t(bucket_id, name)
            WHERE name <> ''
        )
        INSERT INTO storage.prefixes (bucket_id, name)
        SELECT c.bucket_id, c.name
        FROM candidates c
        ON CONFLICT DO NOTHING;
    END IF;

    -- 4) Prune source prefixes bottom-up for OLD−NEW
    IF array_length(v_src_bucket_ids, 1) IS NOT NULL THEN
        -- re-entrancy guard so DELETE on prefixes won't recurse
        IF current_setting('storage.gc.prefixes', true) <> '1' THEN
            PERFORM set_config('storage.gc.prefixes', '1', true);
        END IF;

        PERFORM storage.delete_leaf_prefixes(v_src_bucket_ids, v_src_names);
    END IF;

    RETURN NULL;
END;
$$;


--
-- Name: objects_update_level_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_update_level_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Ensure this is an update operation and the name has changed
    IF TG_OP = 'UPDATE' AND (NEW."name" <> OLD."name" OR NEW."bucket_id" <> OLD."bucket_id") THEN
        -- Set the new level
        NEW."level" := "storage"."get_level"(NEW."name");
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: objects_update_prefix_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.objects_update_prefix_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    old_prefixes TEXT[];
BEGIN
    -- Ensure this is an update operation and the name has changed
    IF TG_OP = 'UPDATE' AND (NEW."name" <> OLD."name" OR NEW."bucket_id" <> OLD."bucket_id") THEN
        -- Retrieve old prefixes
        old_prefixes := "storage"."get_prefixes"(OLD."name");

        -- Remove old prefixes that are only used by this object
        WITH all_prefixes as (
            SELECT unnest(old_prefixes) as prefix
        ),
        can_delete_prefixes as (
             SELECT prefix
             FROM all_prefixes
             WHERE NOT EXISTS (
                 SELECT 1 FROM "storage"."objects"
                 WHERE "bucket_id" = OLD."bucket_id"
                   AND "name" <> OLD."name"
                   AND "name" LIKE (prefix || '%')
             )
         )
        DELETE FROM "storage"."prefixes" WHERE name IN (SELECT prefix FROM can_delete_prefixes);

        -- Add new prefixes
        PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    END IF;
    -- Set the new level
    NEW."level" := "storage"."get_level"(NEW."name");

    RETURN NEW;
END;
$$;


--
-- Name: operation(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.operation() RETURNS text
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN current_setting('storage.operation', true);
END;
$$;


--
-- Name: prefixes_delete_cleanup(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.prefixes_delete_cleanup() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    v_bucket_ids text[];
    v_names      text[];
BEGIN
    IF current_setting('storage.gc.prefixes', true) = '1' THEN
        RETURN NULL;
    END IF;

    PERFORM set_config('storage.gc.prefixes', '1', true);

    SELECT COALESCE(array_agg(d.bucket_id), '{}'),
           COALESCE(array_agg(d.name), '{}')
    INTO v_bucket_ids, v_names
    FROM deleted AS d
    WHERE d.name <> '';

    PERFORM storage.lock_top_prefixes(v_bucket_ids, v_names);
    PERFORM storage.delete_leaf_prefixes(v_bucket_ids, v_names);

    RETURN NULL;
END;
$$;


--
-- Name: prefixes_insert_trigger(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.prefixes_insert_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    RETURN NEW;
END;
$$;


--
-- Name: search(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql
    AS $$
declare
    can_bypass_rls BOOLEAN;
begin
    SELECT rolbypassrls
    INTO can_bypass_rls
    FROM pg_roles
    WHERE rolname = coalesce(nullif(current_setting('role', true), 'none'), current_user);

    IF can_bypass_rls THEN
        RETURN QUERY SELECT * FROM storage.search_v1_optimised(prefix, bucketname, limits, levels, offsets, search, sortcolumn, sortorder);
    ELSE
        RETURN QUERY SELECT * FROM storage.search_legacy_v1(prefix, bucketname, limits, levels, offsets, search, sortcolumn, sortorder);
    END IF;
end;
$$;


--
-- Name: search_legacy_v1(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_legacy_v1(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
declare
    v_order_by text;
    v_sort_order text;
begin
    case
        when sortcolumn = 'name' then
            v_order_by = 'name';
        when sortcolumn = 'updated_at' then
            v_order_by = 'updated_at';
        when sortcolumn = 'created_at' then
            v_order_by = 'created_at';
        when sortcolumn = 'last_accessed_at' then
            v_order_by = 'last_accessed_at';
        else
            v_order_by = 'name';
        end case;

    case
        when sortorder = 'asc' then
            v_sort_order = 'asc';
        when sortorder = 'desc' then
            v_sort_order = 'desc';
        else
            v_sort_order = 'asc';
        end case;

    v_order_by = v_order_by || ' ' || v_sort_order;

    return query execute
        'with folders as (
           select path_tokens[$1] as folder
           from storage.objects
             where objects.name ilike $2 || $3 || ''%''
               and bucket_id = $4
               and array_length(objects.path_tokens, 1) <> $1
           group by folder
           order by folder ' || v_sort_order || '
     )
     (select folder as "name",
            null as id,
            null as updated_at,
            null as created_at,
            null as last_accessed_at,
            null as metadata from folders)
     union all
     (select path_tokens[$1] as "name",
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
     from storage.objects
     where objects.name ilike $2 || $3 || ''%''
       and bucket_id = $4
       and array_length(objects.path_tokens, 1) = $1
     order by ' || v_order_by || ')
     limit $5
     offset $6' using levels, prefix, search, bucketname, limits, offsets;
end;
$_$;


--
-- Name: search_v1_optimised(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_v1_optimised(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
declare
    v_order_by text;
    v_sort_order text;
begin
    case
        when sortcolumn = 'name' then
            v_order_by = 'name';
        when sortcolumn = 'updated_at' then
            v_order_by = 'updated_at';
        when sortcolumn = 'created_at' then
            v_order_by = 'created_at';
        when sortcolumn = 'last_accessed_at' then
            v_order_by = 'last_accessed_at';
        else
            v_order_by = 'name';
        end case;

    case
        when sortorder = 'asc' then
            v_sort_order = 'asc';
        when sortorder = 'desc' then
            v_sort_order = 'desc';
        else
            v_sort_order = 'asc';
        end case;

    v_order_by = v_order_by || ' ' || v_sort_order;

    return query execute
        'with folders as (
           select (string_to_array(name, ''/''))[level] as name
           from storage.prefixes
             where lower(prefixes.name) like lower($2 || $3) || ''%''
               and bucket_id = $4
               and level = $1
           order by name ' || v_sort_order || '
     )
     (select name,
            null as id,
            null as updated_at,
            null as created_at,
            null as last_accessed_at,
            null as metadata from folders)
     union all
     (select path_tokens[level] as "name",
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
     from storage.objects
     where lower(objects.name) like lower($2 || $3) || ''%''
       and bucket_id = $4
       and level = $1
     order by ' || v_order_by || ')
     limit $5
     offset $6' using levels, prefix, search, bucketname, limits, offsets;
end;
$_$;


--
-- Name: search_v2(text, text, integer, integer, text, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_v2(prefix text, bucket_name text, limits integer DEFAULT 100, levels integer DEFAULT 1, start_after text DEFAULT ''::text, sort_order text DEFAULT 'asc'::text, sort_column text DEFAULT 'name'::text, sort_column_after text DEFAULT ''::text) RETURNS TABLE(key text, name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
DECLARE
    sort_col text;
    sort_ord text;
    cursor_op text;
    cursor_expr text;
    sort_expr text;
BEGIN
    -- Validate sort_order
    sort_ord := lower(sort_order);
    IF sort_ord NOT IN ('asc', 'desc') THEN
        sort_ord := 'asc';
    END IF;

    -- Determine cursor comparison operator
    IF sort_ord = 'asc' THEN
        cursor_op := '>';
    ELSE
        cursor_op := '<';
    END IF;
    
    sort_col := lower(sort_column);
    -- Validate sort column  
    IF sort_col IN ('updated_at', 'created_at') THEN
        cursor_expr := format(
            '($5 = '''' OR ROW(date_trunc(''milliseconds'', %I), name COLLATE "C") %s ROW(COALESCE(NULLIF($6, '''')::timestamptz, ''epoch''::timestamptz), $5))',
            sort_col, cursor_op
        );
        sort_expr := format(
            'COALESCE(date_trunc(''milliseconds'', %I), ''epoch''::timestamptz) %s, name COLLATE "C" %s',
            sort_col, sort_ord, sort_ord
        );
    ELSE
        cursor_expr := format('($5 = '''' OR name COLLATE "C" %s $5)', cursor_op);
        sort_expr := format('name COLLATE "C" %s', sort_ord);
    END IF;

    RETURN QUERY EXECUTE format(
        $sql$
        SELECT * FROM (
            (
                SELECT
                    split_part(name, '/', $4) AS key,
                    name,
                    NULL::uuid AS id,
                    updated_at,
                    created_at,
                    NULL::timestamptz AS last_accessed_at,
                    NULL::jsonb AS metadata
                FROM storage.prefixes
                WHERE name COLLATE "C" LIKE $1 || '%%'
                    AND bucket_id = $2
                    AND level = $4
                    AND %s
                ORDER BY %s
                LIMIT $3
            )
            UNION ALL
            (
                SELECT
                    split_part(name, '/', $4) AS key,
                    name,
                    id,
                    updated_at,
                    created_at,
                    last_accessed_at,
                    metadata
                FROM storage.objects
                WHERE name COLLATE "C" LIKE $1 || '%%'
                    AND bucket_id = $2
                    AND level = $4
                    AND %s
                ORDER BY %s
                LIMIT $3
            )
        ) obj
        ORDER BY %s
        LIMIT $3
        $sql$,
        cursor_expr,    -- prefixes WHERE
        sort_expr,      -- prefixes ORDER BY
        cursor_expr,    -- objects WHERE
        sort_expr,      -- objects ORDER BY
        sort_expr       -- final ORDER BY
    )
    USING prefix, bucket_name, limits, levels, start_after, sort_column_after;
END;
$_$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW; 
END;
$$;


--
-- Name: audit_log_entries; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.audit_log_entries (
    instance_id uuid,
    id uuid NOT NULL,
    payload json,
    created_at timestamp with time zone,
    ip_address character varying(64) DEFAULT ''::character varying NOT NULL
);


--
-- Name: TABLE audit_log_entries; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.audit_log_entries IS 'Auth: Audit trail for user actions.';


--
-- Name: flow_state; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.flow_state (
    id uuid NOT NULL,
    user_id uuid,
    auth_code text NOT NULL,
    code_challenge_method auth.code_challenge_method NOT NULL,
    code_challenge text NOT NULL,
    provider_type text NOT NULL,
    provider_access_token text,
    provider_refresh_token text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    authentication_method text NOT NULL,
    auth_code_issued_at timestamp with time zone
);


--
-- Name: TABLE flow_state; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.flow_state IS 'stores metadata for pkce logins';


--
-- Name: identities; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.identities (
    provider_id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    email text GENERATED ALWAYS AS (lower((identity_data ->> 'email'::text))) STORED,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


--
-- Name: TABLE identities; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.identities IS 'Auth: Stores identities associated to a user.';


--
-- Name: COLUMN identities.email; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.identities.email IS 'Auth: Email is a generated column that references the optional email property in the identity_data';


--
-- Name: instances; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.instances (
    id uuid NOT NULL,
    uuid uuid,
    raw_base_config text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: TABLE instances; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.instances IS 'Auth: Manages users across multiple sites.';


--
-- Name: mfa_amr_claims; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_amr_claims (
    session_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    authentication_method text NOT NULL,
    id uuid NOT NULL
);


--
-- Name: TABLE mfa_amr_claims; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_amr_claims IS 'auth: stores authenticator method reference claims for multi factor authentication';


--
-- Name: mfa_challenges; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_challenges (
    id uuid NOT NULL,
    factor_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    verified_at timestamp with time zone,
    ip_address inet NOT NULL,
    otp_code text,
    web_authn_session_data jsonb
);


--
-- Name: TABLE mfa_challenges; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_challenges IS 'auth: stores metadata about challenge requests made';


--
-- Name: mfa_factors; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_factors (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    friendly_name text,
    factor_type auth.factor_type NOT NULL,
    status auth.factor_status NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    secret text,
    phone text,
    last_challenged_at timestamp with time zone,
    web_authn_credential jsonb,
    web_authn_aaguid uuid,
    last_webauthn_challenge_data jsonb
);


--
-- Name: TABLE mfa_factors; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_factors IS 'auth: stores metadata about factors';


--
-- Name: COLUMN mfa_factors.last_webauthn_challenge_data; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.mfa_factors.last_webauthn_challenge_data IS 'Stores the latest WebAuthn challenge data including attestation/assertion for customer verification';


--
-- Name: oauth_authorizations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_authorizations (
    id uuid NOT NULL,
    authorization_id text NOT NULL,
    client_id uuid NOT NULL,
    user_id uuid,
    redirect_uri text NOT NULL,
    scope text NOT NULL,
    state text,
    resource text,
    code_challenge text,
    code_challenge_method auth.code_challenge_method,
    response_type auth.oauth_response_type DEFAULT 'code'::auth.oauth_response_type NOT NULL,
    status auth.oauth_authorization_status DEFAULT 'pending'::auth.oauth_authorization_status NOT NULL,
    authorization_code text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone DEFAULT (now() + '00:03:00'::interval) NOT NULL,
    approved_at timestamp with time zone,
    nonce text,
    CONSTRAINT oauth_authorizations_authorization_code_length CHECK ((char_length(authorization_code) <= 255)),
    CONSTRAINT oauth_authorizations_code_challenge_length CHECK ((char_length(code_challenge) <= 128)),
    CONSTRAINT oauth_authorizations_expires_at_future CHECK ((expires_at > created_at)),
    CONSTRAINT oauth_authorizations_nonce_length CHECK ((char_length(nonce) <= 255)),
    CONSTRAINT oauth_authorizations_redirect_uri_length CHECK ((char_length(redirect_uri) <= 2048)),
    CONSTRAINT oauth_authorizations_resource_length CHECK ((char_length(resource) <= 2048)),
    CONSTRAINT oauth_authorizations_scope_length CHECK ((char_length(scope) <= 4096)),
    CONSTRAINT oauth_authorizations_state_length CHECK ((char_length(state) <= 4096))
);


--
-- Name: oauth_clients; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_clients (
    id uuid NOT NULL,
    client_secret_hash text,
    registration_type auth.oauth_registration_type NOT NULL,
    redirect_uris text NOT NULL,
    grant_types text NOT NULL,
    client_name text,
    client_uri text,
    logo_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    client_type auth.oauth_client_type DEFAULT 'confidential'::auth.oauth_client_type NOT NULL,
    CONSTRAINT oauth_clients_client_name_length CHECK ((char_length(client_name) <= 1024)),
    CONSTRAINT oauth_clients_client_uri_length CHECK ((char_length(client_uri) <= 2048)),
    CONSTRAINT oauth_clients_logo_uri_length CHECK ((char_length(logo_uri) <= 2048))
);


--
-- Name: oauth_consents; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_consents (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    client_id uuid NOT NULL,
    scopes text NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    CONSTRAINT oauth_consents_revoked_after_granted CHECK (((revoked_at IS NULL) OR (revoked_at >= granted_at))),
    CONSTRAINT oauth_consents_scopes_length CHECK ((char_length(scopes) <= 2048)),
    CONSTRAINT oauth_consents_scopes_not_empty CHECK ((char_length(TRIM(BOTH FROM scopes)) > 0))
);


--
-- Name: one_time_tokens; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.one_time_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token_type auth.one_time_token_type NOT NULL,
    token_hash text NOT NULL,
    relates_to text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT one_time_tokens_token_hash_check CHECK ((char_length(token_hash) > 0))
);


--
-- Name: refresh_tokens; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.refresh_tokens (
    instance_id uuid,
    id bigint NOT NULL,
    token character varying(255),
    user_id character varying(255),
    revoked boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    parent character varying(255),
    session_id uuid
);


--
-- Name: TABLE refresh_tokens; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.refresh_tokens IS 'Auth: Store of tokens used to refresh JWT tokens once they expire.';


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.refresh_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.refresh_tokens_id_seq OWNED BY auth.refresh_tokens.id;


--
-- Name: saml_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.saml_providers (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    entity_id text NOT NULL,
    metadata_xml text NOT NULL,
    metadata_url text,
    attribute_mapping jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    name_id_format text,
    CONSTRAINT "entity_id not empty" CHECK ((char_length(entity_id) > 0)),
    CONSTRAINT "metadata_url not empty" CHECK (((metadata_url = NULL::text) OR (char_length(metadata_url) > 0))),
    CONSTRAINT "metadata_xml not empty" CHECK ((char_length(metadata_xml) > 0))
);


--
-- Name: TABLE saml_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_providers IS 'Auth: Manages SAML Identity Provider connections.';


--
-- Name: saml_relay_states; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.saml_relay_states (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    request_id text NOT NULL,
    for_email text,
    redirect_to text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    flow_state_id uuid,
    CONSTRAINT "request_id not empty" CHECK ((char_length(request_id) > 0))
);


--
-- Name: TABLE saml_relay_states; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_relay_states IS 'Auth: Contains SAML Relay State information for each Service Provider initiated login.';


--
-- Name: schema_migrations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: TABLE schema_migrations; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.schema_migrations IS 'Auth: Manages updates to the auth system.';


--
-- Name: sessions; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    factor_id uuid,
    aal auth.aal_level,
    not_after timestamp with time zone,
    refreshed_at timestamp without time zone,
    user_agent text,
    ip inet,
    tag text,
    oauth_client_id uuid,
    refresh_token_hmac_key text,
    refresh_token_counter bigint,
    scopes text,
    CONSTRAINT sessions_scopes_length CHECK ((char_length(scopes) <= 4096))
);


--
-- Name: TABLE sessions; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sessions IS 'Auth: Stores session data associated to a user.';


--
-- Name: COLUMN sessions.not_after; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.not_after IS 'Auth: Not after is a nullable column that contains a timestamp after which the session should be regarded as expired.';


--
-- Name: COLUMN sessions.refresh_token_hmac_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_hmac_key IS 'Holds a HMAC-SHA256 key used to sign refresh tokens for this session.';


--
-- Name: COLUMN sessions.refresh_token_counter; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_counter IS 'Holds the ID (counter) of the last issued refresh token.';


--
-- Name: sso_domains; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_domains (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    domain text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT "domain not empty" CHECK ((char_length(domain) > 0))
);


--
-- Name: TABLE sso_domains; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_domains IS 'Auth: Manages SSO email address domain mapping to an SSO Identity Provider.';


--
-- Name: sso_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_providers (
    id uuid NOT NULL,
    resource_id text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    disabled boolean,
    CONSTRAINT "resource_id not empty" CHECK (((resource_id = NULL::text) OR (char_length(resource_id) > 0)))
);


--
-- Name: TABLE sso_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_providers IS 'Auth: Manages SSO identity provider information; see saml_providers for SAML.';


--
-- Name: COLUMN sso_providers.resource_id; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sso_providers.resource_id IS 'Auth: Uniquely identifies a SSO provider according to a user-chosen resource ID (case insensitive), useful in infrastructure as code.';


--
-- Name: users; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.users (
    instance_id uuid,
    id uuid NOT NULL,
    aud character varying(255),
    role character varying(255),
    email character varying(255),
    encrypted_password character varying(255),
    email_confirmed_at timestamp with time zone,
    invited_at timestamp with time zone,
    confirmation_token character varying(255),
    confirmation_sent_at timestamp with time zone,
    recovery_token character varying(255),
    recovery_sent_at timestamp with time zone,
    email_change_token_new character varying(255),
    email_change character varying(255),
    email_change_sent_at timestamp with time zone,
    last_sign_in_at timestamp with time zone,
    raw_app_meta_data jsonb,
    raw_user_meta_data jsonb,
    is_super_admin boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    phone text DEFAULT NULL::character varying,
    phone_confirmed_at timestamp with time zone,
    phone_change text DEFAULT ''::character varying,
    phone_change_token character varying(255) DEFAULT ''::character varying,
    phone_change_sent_at timestamp with time zone,
    confirmed_at timestamp with time zone GENERATED ALWAYS AS (LEAST(email_confirmed_at, phone_confirmed_at)) STORED,
    email_change_token_current character varying(255) DEFAULT ''::character varying,
    email_change_confirm_status smallint DEFAULT 0,
    banned_until timestamp with time zone,
    reauthentication_token character varying(255) DEFAULT ''::character varying,
    reauthentication_sent_at timestamp with time zone,
    is_sso_user boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    is_anonymous boolean DEFAULT false NOT NULL,
    CONSTRAINT users_email_change_confirm_status_check CHECK (((email_change_confirm_status >= 0) AND (email_change_confirm_status <= 2)))
);


--
-- Name: TABLE users; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.users IS 'Auth: Stores user login data within a secure schema.';


--
-- Name: COLUMN users.is_sso_user; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.users.is_sso_user IS 'Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.';


--
-- Name: cookbook_folders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cookbook_folders (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    cookbook_id uuid NOT NULL,
    parent_folder_id uuid,
    name character varying(100) NOT NULL,
    "order" integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: cookbook_recipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cookbook_recipes (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    cookbook_id uuid NOT NULL,
    recipe_id uuid NOT NULL,
    "order" integer DEFAULT 0,
    added_at timestamp with time zone DEFAULT now()
);


--
-- Name: cookbook_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cookbook_shares (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    cookbook_id uuid NOT NULL,
    shared_by_user_id uuid NOT NULL,
    shared_with_user_id uuid NOT NULL,
    permission_level character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT cookbook_shares_permission_level_check CHECK (((permission_level)::text = ANY ((ARRAY['view'::character varying, 'fork'::character varying, 'collaborate'::character varying])::text[])))
);


--
-- Name: cookbooks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cookbooks (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    title character varying(200) NOT NULL,
    subtitle character varying(500),
    description text,
    image_url text,
    is_public boolean DEFAULT false,
    recipe_count integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: featured_recipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.featured_recipes (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    recipe_id uuid NOT NULL,
    featured_type character varying(20) NOT NULL,
    priority integer DEFAULT 0,
    start_date timestamp with time zone,
    end_date timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT featured_recipes_featured_type_check CHECK (((featured_type)::text = ANY ((ARRAY['manual'::character varying, 'trending'::character varying, 'popular'::character varying, 'time_of_day'::character varying])::text[])))
);


--
-- Name: folder_recipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.folder_recipes (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    folder_id uuid NOT NULL,
    recipe_id uuid NOT NULL,
    "order" integer DEFAULT 0,
    added_at timestamp with time zone DEFAULT now()
);


--
-- Name: recipe_contributors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipe_contributors (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    recipe_id uuid NOT NULL,
    user_id uuid,
    contribution_type character varying(20) NOT NULL,
    "order" integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    display_name character varying(100) DEFAULT NULL::character varying,
    CONSTRAINT recipe_contributors_contribution_type_check CHECK (((contribution_type)::text = ANY ((ARRAY['creator'::character varying, 'fork'::character varying, 'edit'::character varying])::text[])))
);


--
-- Name: COLUMN recipe_contributors.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_contributors.display_name IS 'Display name for deleted users. When a user deletes their account, this stores "[Deleted User]" and user_id is set to NULL.';


--
-- Name: recipe_cooking_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipe_cooking_events (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    recipe_id uuid NOT NULL,
    cooked_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    rating numeric(2,1),
    image_url text,
    duration_minutes integer,
    CONSTRAINT recipe_cooking_events_duration_minutes_check CHECK (((duration_minutes IS NULL) OR (duration_minutes >= 0))),
    CONSTRAINT recipe_cooking_events_rating_check CHECK (((rating IS NULL) OR ((rating >= 0.5) AND (rating <= 5.0))))
);


--
-- Name: TABLE recipe_cooking_events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.recipe_cooking_events IS 'Event log tracking every time a user cooks a recipe. Enables time-based popularity queries and trend analysis.';


--
-- Name: COLUMN recipe_cooking_events.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.id IS 'Unique identifier for this cooking event';


--
-- Name: COLUMN recipe_cooking_events.user_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.user_id IS 'User who cooked the recipe';


--
-- Name: COLUMN recipe_cooking_events.recipe_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.recipe_id IS 'Recipe that was cooked';


--
-- Name: COLUMN recipe_cooking_events.cooked_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.cooked_at IS 'Timestamp when the recipe was cooked (defaults to NOW())';


--
-- Name: COLUMN recipe_cooking_events.created_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.created_at IS 'Timestamp when this event was recorded in the system';


--
-- Name: COLUMN recipe_cooking_events.rating; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.rating IS 'Rating given at this specific cooking session (0.5-5.0). May differ from user_recipe_data.rating which is the current/latest rating.';


--
-- Name: COLUMN recipe_cooking_events.image_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.image_url IS 'URL to a photo taken during this cooking session, stored in cooking-events bucket.';


--
-- Name: COLUMN recipe_cooking_events.duration_minutes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipe_cooking_events.duration_minutes IS 'Actual cooking duration in minutes for this session, tracked by the app timer.';


--
-- Name: recipe_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipe_shares (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    recipe_id uuid NOT NULL,
    shared_by_user_id uuid NOT NULL,
    shared_with_user_id uuid NOT NULL,
    permission_level character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT recipe_shares_permission_level_check CHECK (((permission_level)::text = ANY ((ARRAY['view'::character varying, 'fork'::character varying, 'collaborate'::character varying])::text[])))
);


--
-- Name: recipes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipes (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    image_url text,
    ingredients jsonb DEFAULT '[]'::jsonb NOT NULL,
    instructions jsonb DEFAULT '[]'::jsonb NOT NULL,
    servings integer,
    difficulty character varying(20),
    tags text[] DEFAULT ARRAY[]::text[],
    categories text[] DEFAULT ARRAY[]::text[],
    prep_time_minutes integer,
    cook_time_minutes integer,
    total_time_minutes integer,
    source_type character varying(20) NOT NULL,
    source_url text,
    created_by uuid NOT NULL,
    original_recipe_id uuid,
    fork_count integer DEFAULT 0,
    is_public boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    language character varying(2) DEFAULT 'en'::character varying,
    search_vector tsvector,
    average_rating numeric(3,2),
    rating_count integer DEFAULT 0,
    rating_distribution jsonb DEFAULT '{"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "0.5": 0, "1.5": 0, "2.5": 0, "3.5": 0, "4.5": 0}'::jsonb,
    total_times_cooked integer DEFAULT 0,
    is_draft boolean DEFAULT false NOT NULL,
    image_source character varying(50),
    CONSTRAINT recipes_average_rating_check CHECK (((average_rating >= 0.50) AND (average_rating <= 5.00))),
    CONSTRAINT recipes_difficulty_check CHECK (((difficulty)::text = ANY ((ARRAY['easy'::character varying, 'medium'::character varying, 'hard'::character varying])::text[]))),
    CONSTRAINT recipes_rating_count_check CHECK ((rating_count >= 0)),
    CONSTRAINT recipes_servings_check CHECK ((servings > 0)),
    CONSTRAINT recipes_source_type_check CHECK (((source_type)::text = ANY ((ARRAY['video'::character varying, 'photo'::character varying, 'voice'::character varying, 'url'::character varying, 'paste'::character varying, 'link'::character varying])::text[]))),
    CONSTRAINT recipes_total_times_cooked_check CHECK ((total_times_cooked >= 0))
);


--
-- Name: COLUMN recipes.language; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.language IS 'ISO 639-1 language code (en, fr, etc.) used to select appropriate full-text search dictionary';


--
-- Name: COLUMN recipes.search_vector; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.search_vector IS 'Language-aware full-text search vector with relevance weights';


--
-- Name: COLUMN recipes.average_rating; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.average_rating IS 'Calculated average of all user ratings for this recipe. NULL if no ratings. Scale: 0.50-5.00 with half-star support';


--
-- Name: COLUMN recipes.rating_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.rating_count IS 'Total number of user ratings for this recipe. Used for popularity metrics and confidence in average_rating.';


--
-- Name: COLUMN recipes.rating_distribution; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.rating_distribution IS 'JSONB object tracking count of ratings at each half-star level (0.5-5.0). Format: {"0.5": count, "1": count, "1.5": count, ...}. Supports half-star ratings. Enables rating histogram display and detailed analytics.';


--
-- Name: COLUMN recipes.total_times_cooked; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.total_times_cooked IS 'Total number of times this recipe has been cooked by all users. Updated automatically via trigger when user_recipe_data.times_cooked changes.';


--
-- Name: COLUMN recipes.is_draft; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.is_draft IS 'Draft recipes are only visible to owner. Set to false when user saves.';


--
-- Name: COLUMN recipes.image_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipes.image_source IS 'Source of the recipe image: video_thumbnail, scraped, generated, uploaded';


--
-- Name: user_onboarding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_onboarding (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    heard_from text NOT NULL,
    cooking_frequency text NOT NULL,
    recipe_sources text[] NOT NULL,
    display_name text,
    completed_at timestamp with time zone DEFAULT now(),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    age integer,
    CONSTRAINT age_range_check CHECK (((age IS NULL) OR ((age >= 13) AND (age <= 120))))
);


--
-- Name: TABLE user_onboarding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.user_onboarding IS 'Stores user onboarding questionnaire responses for analytics and personalization';


--
-- Name: COLUMN user_onboarding.heard_from; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_onboarding.heard_from IS 'Marketing source: how user discovered the app';


--
-- Name: COLUMN user_onboarding.cooking_frequency; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_onboarding.cooking_frequency IS 'User cooking habits: rarely, occasionally, regularly, almost_daily';


--
-- Name: COLUMN user_onboarding.recipe_sources; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_onboarding.recipe_sources IS 'Where user currently gets recipes: tiktok, instagram, youtube, blogs, etc';


--
-- Name: COLUMN user_onboarding.display_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_onboarding.display_name IS 'Optional display name chosen during onboarding';


--
-- Name: COLUMN user_onboarding.age; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_onboarding.age IS 'User age (optional, 13-120 years old)';


--
-- Name: user_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_preferences (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    heard_from text NOT NULL,
    cooking_frequency text NOT NULL,
    recipe_sources text[] NOT NULL,
    display_name text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: user_recipe_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_recipe_data (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    recipe_id uuid NOT NULL,
    rating numeric(2,1),
    custom_prep_time_minutes integer,
    custom_cook_time_minutes integer,
    custom_difficulty character varying(20),
    notes text,
    custom_servings integer,
    times_cooked integer DEFAULT 0,
    last_cooked_at timestamp with time zone,
    is_favorite boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    was_extracted boolean DEFAULT false NOT NULL,
    CONSTRAINT user_recipe_data_custom_difficulty_check CHECK (((custom_difficulty)::text = ANY ((ARRAY['easy'::character varying, 'medium'::character varying, 'hard'::character varying])::text[]))),
    CONSTRAINT user_recipe_data_rating_check CHECK (((rating IS NULL) OR ((rating >= 0.5) AND (rating <= 5.0) AND ((rating * (2)::numeric) = floor((rating * (2)::numeric))))))
);


--
-- Name: COLUMN user_recipe_data.is_favorite; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_recipe_data.is_favorite IS 'True if this user favorited this recipe. Used for the "Favorites" virtual collection.';


--
-- Name: COLUMN user_recipe_data.was_extracted; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_recipe_data.was_extracted IS 'True if this user extracted/imported this recipe. Used for the "Extracted" virtual collection.';


--
-- Name: CONSTRAINT user_recipe_data_rating_check ON user_recipe_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON CONSTRAINT user_recipe_data_rating_check ON public.user_recipe_data IS 'Ensures rating is between 0.5 and 5.0 in half-star increments (0.5, 1.0, 1.5, ..., 5.0)';


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    name character varying(100),
    profile_completed boolean DEFAULT true,
    avatar_url text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    onboarding_completed boolean DEFAULT false,
    CONSTRAINT name_not_empty CHECK ((char_length(TRIM(BOTH FROM name)) >= 1))
);


--
-- Name: TABLE users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.users IS 'Application user profiles. Links to auth.users via id. Stores app-specific data only - authentication data lives in auth.users.';


--
-- Name: COLUMN users.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.id IS 'References auth.users.id (one-to-one)';


--
-- Name: COLUMN users.name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.name IS 'User display name (optional - defaults to display_name from onboarding or email username)';


--
-- Name: COLUMN users.profile_completed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.profile_completed IS 'Whether user has completed optional profile setup (future feature)';


--
-- Name: COLUMN users.avatar_url; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.avatar_url IS 'Profile picture URL stored in Supabase Storage (optional)';


--
-- Name: COLUMN users.onboarding_completed; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.onboarding_completed IS 'Whether user has completed required onboarding questionnaire (controls is_new_user flag)';


--
-- Name: video_creators; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_creators (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    platform character varying(50) NOT NULL,
    platform_user_id character varying(255) NOT NULL,
    platform_username character varying(255),
    display_name character varying(255),
    profile_url text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: video_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.video_sources (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    platform character varying(50) NOT NULL,
    platform_video_id character varying(255) NOT NULL,
    recipe_id uuid,
    video_creator_id uuid,
    original_url text NOT NULL,
    canonical_url text,
    title text,
    description text,
    duration_seconds integer,
    thumbnail_url text,
    view_count bigint,
    like_count bigint,
    upload_date timestamp with time zone,
    raw_metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: waitlist; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.waitlist (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email text NOT NULL,
    source text DEFAULT 'landing'::text,
    ip_address text,
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    utm_source text,
    utm_medium text,
    utm_campaign text,
    referrer text
);


--
-- Name: TABLE waitlist; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.waitlist IS 'Stores email signups from the landing page waitlist';


--
-- Name: COLUMN waitlist.utm_source; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.waitlist.utm_source IS 'Traffic source (e.g., instagram, twitter, tiktok)';


--
-- Name: COLUMN waitlist.utm_medium; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.waitlist.utm_medium IS 'Marketing medium (e.g., social, email, cpc)';


--
-- Name: COLUMN waitlist.utm_campaign; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.waitlist.utm_campaign IS 'Campaign name (e.g., launch, collab_chef)';


--
-- Name: COLUMN waitlist.referrer; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.waitlist.referrer IS 'HTTP referrer header';


--
-- Name: messages; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
)
PARTITION BY RANGE (inserted_at);


--
-- Name: schema_migrations; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);


--
-- Name: subscription; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.subscription (
    id bigint NOT NULL,
    subscription_id uuid NOT NULL,
    entity regclass NOT NULL,
    filters realtime.user_defined_filter[] DEFAULT '{}'::realtime.user_defined_filter[] NOT NULL,
    claims jsonb NOT NULL,
    claims_role regrole GENERATED ALWAYS AS (realtime.to_regrole((claims ->> 'role'::text))) STORED NOT NULL,
    created_at timestamp without time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);


--
-- Name: subscription_id_seq; Type: SEQUENCE; Schema: realtime; Owner: -
--

ALTER TABLE realtime.subscription ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME realtime.subscription_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: buckets; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets (
    id text NOT NULL,
    name text NOT NULL,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    public boolean DEFAULT false,
    avif_autodetection boolean DEFAULT false,
    file_size_limit bigint,
    allowed_mime_types text[],
    owner_id text,
    type storage.buckettype DEFAULT 'STANDARD'::storage.buckettype NOT NULL
);


--
-- Name: COLUMN buckets.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.buckets.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: buckets_analytics; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_analytics (
    name text NOT NULL,
    type storage.buckettype DEFAULT 'ANALYTICS'::storage.buckettype NOT NULL,
    format text DEFAULT 'ICEBERG'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: buckets_vectors; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_vectors (
    id text NOT NULL,
    type storage.buckettype DEFAULT 'VECTOR'::storage.buckettype NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: migrations; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: objects; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.objects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_id text,
    name text,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_accessed_at timestamp with time zone DEFAULT now(),
    metadata jsonb,
    path_tokens text[] GENERATED ALWAYS AS (string_to_array(name, '/'::text)) STORED,
    version text,
    owner_id text,
    user_metadata jsonb,
    level integer
);


--
-- Name: COLUMN objects.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.objects.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: prefixes; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.prefixes (
    bucket_id text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    level integer GENERATED ALWAYS AS (storage.get_level(name)) STORED NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: s3_multipart_uploads; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.s3_multipart_uploads (
    id text NOT NULL,
    in_progress_size bigint DEFAULT 0 NOT NULL,
    upload_signature text NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    version text NOT NULL,
    owner_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_metadata jsonb
);


--
-- Name: s3_multipart_uploads_parts; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.s3_multipart_uploads_parts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    upload_id text NOT NULL,
    size bigint DEFAULT 0 NOT NULL,
    part_number integer NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    etag text NOT NULL,
    owner_id text,
    version text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: vector_indexes; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.vector_indexes (
    id text DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    bucket_id text NOT NULL,
    data_type text NOT NULL,
    dimension integer NOT NULL,
    distance_metric text NOT NULL,
    metadata_configuration jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: schema_migrations; Type: TABLE; Schema: supabase_migrations; Owner: -
--

CREATE TABLE supabase_migrations.schema_migrations (
    version text NOT NULL,
    statements text[],
    name text,
    created_by text,
    idempotency_key text,
    rollback text[]
);


--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass);


--
-- Name: mfa_amr_claims amr_id_pk; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT amr_id_pk PRIMARY KEY (id);


--
-- Name: audit_log_entries audit_log_entries_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.audit_log_entries
    ADD CONSTRAINT audit_log_entries_pkey PRIMARY KEY (id);


--
-- Name: flow_state flow_state_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.flow_state
    ADD CONSTRAINT flow_state_pkey PRIMARY KEY (id);


--
-- Name: identities identities_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_pkey PRIMARY KEY (id);


--
-- Name: identities identities_provider_id_provider_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_provider_id_provider_unique UNIQUE (provider_id, provider);


--
-- Name: instances instances_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.instances
    ADD CONSTRAINT instances_pkey PRIMARY KEY (id);


--
-- Name: mfa_amr_claims mfa_amr_claims_session_id_authentication_method_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_authentication_method_pkey UNIQUE (session_id, authentication_method);


--
-- Name: mfa_challenges mfa_challenges_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_pkey PRIMARY KEY (id);


--
-- Name: mfa_factors mfa_factors_last_challenged_at_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_last_challenged_at_key UNIQUE (last_challenged_at);


--
-- Name: mfa_factors mfa_factors_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_pkey PRIMARY KEY (id);


--
-- Name: oauth_authorizations oauth_authorizations_authorization_code_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_authorization_code_key UNIQUE (authorization_code);


--
-- Name: oauth_authorizations oauth_authorizations_authorization_id_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_authorization_id_key UNIQUE (authorization_id);


--
-- Name: oauth_authorizations oauth_authorizations_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_pkey PRIMARY KEY (id);


--
-- Name: oauth_clients oauth_clients_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_clients
    ADD CONSTRAINT oauth_clients_pkey PRIMARY KEY (id);


--
-- Name: oauth_consents oauth_consents_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_pkey PRIMARY KEY (id);


--
-- Name: oauth_consents oauth_consents_user_client_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_user_client_unique UNIQUE (user_id, client_id);


--
-- Name: one_time_tokens one_time_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_token_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_unique UNIQUE (token);


--
-- Name: saml_providers saml_providers_entity_id_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_entity_id_key UNIQUE (entity_id);


--
-- Name: saml_providers saml_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_pkey PRIMARY KEY (id);


--
-- Name: saml_relay_states saml_relay_states_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sso_domains sso_domains_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_pkey PRIMARY KEY (id);


--
-- Name: sso_providers sso_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_providers
    ADD CONSTRAINT sso_providers_pkey PRIMARY KEY (id);


--
-- Name: users users_phone_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_phone_key UNIQUE (phone);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: cookbook_folders cookbook_folders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_folders
    ADD CONSTRAINT cookbook_folders_pkey PRIMARY KEY (id);


--
-- Name: cookbook_recipes cookbook_recipes_cookbook_id_recipe_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_recipes
    ADD CONSTRAINT cookbook_recipes_cookbook_id_recipe_id_key UNIQUE (cookbook_id, recipe_id);


--
-- Name: cookbook_recipes cookbook_recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_recipes
    ADD CONSTRAINT cookbook_recipes_pkey PRIMARY KEY (id);


--
-- Name: cookbook_shares cookbook_shares_cookbook_id_shared_with_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_shares
    ADD CONSTRAINT cookbook_shares_cookbook_id_shared_with_user_id_key UNIQUE (cookbook_id, shared_with_user_id);


--
-- Name: cookbook_shares cookbook_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_shares
    ADD CONSTRAINT cookbook_shares_pkey PRIMARY KEY (id);


--
-- Name: cookbooks cookbooks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbooks
    ADD CONSTRAINT cookbooks_pkey PRIMARY KEY (id);


--
-- Name: extraction_jobs extraction_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraction_jobs
    ADD CONSTRAINT extraction_jobs_pkey PRIMARY KEY (id);


--
-- Name: featured_recipes featured_recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.featured_recipes
    ADD CONSTRAINT featured_recipes_pkey PRIMARY KEY (id);


--
-- Name: folder_recipes folder_recipes_folder_id_recipe_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.folder_recipes
    ADD CONSTRAINT folder_recipes_folder_id_recipe_id_key UNIQUE (folder_id, recipe_id);


--
-- Name: folder_recipes folder_recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.folder_recipes
    ADD CONSTRAINT folder_recipes_pkey PRIMARY KEY (id);


--
-- Name: recipe_contributors recipe_contributors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_contributors
    ADD CONSTRAINT recipe_contributors_pkey PRIMARY KEY (id);


--
-- Name: recipe_cooking_events recipe_cooking_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_cooking_events
    ADD CONSTRAINT recipe_cooking_events_pkey PRIMARY KEY (id);


--
-- Name: recipe_shares recipe_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_shares
    ADD CONSTRAINT recipe_shares_pkey PRIMARY KEY (id);


--
-- Name: recipe_shares recipe_shares_recipe_id_shared_with_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_shares
    ADD CONSTRAINT recipe_shares_recipe_id_shared_with_user_id_key UNIQUE (recipe_id, shared_with_user_id);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: user_onboarding user_onboarding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_onboarding
    ADD CONSTRAINT user_onboarding_pkey PRIMARY KEY (id);


--
-- Name: user_onboarding user_onboarding_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_onboarding
    ADD CONSTRAINT user_onboarding_user_id_key UNIQUE (user_id);


--
-- Name: user_preferences user_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_pkey PRIMARY KEY (id);


--
-- Name: user_preferences user_preferences_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_key UNIQUE (user_id);


--
-- Name: user_recipe_data user_recipe_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_recipe_data
    ADD CONSTRAINT user_recipe_data_pkey PRIMARY KEY (id);


--
-- Name: user_recipe_data user_recipe_data_user_id_recipe_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_recipe_data
    ADD CONSTRAINT user_recipe_data_user_id_recipe_id_key UNIQUE (user_id, recipe_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: video_creators video_creators_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_creators
    ADD CONSTRAINT video_creators_pkey PRIMARY KEY (id);


--
-- Name: video_creators video_creators_platform_platform_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_creators
    ADD CONSTRAINT video_creators_platform_platform_user_id_key UNIQUE (platform, platform_user_id);


--
-- Name: video_sources video_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_sources
    ADD CONSTRAINT video_sources_pkey PRIMARY KEY (id);


--
-- Name: video_sources video_sources_platform_platform_video_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_sources
    ADD CONSTRAINT video_sources_platform_platform_video_id_key UNIQUE (platform, platform_video_id);


--
-- Name: waitlist waitlist_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.waitlist
    ADD CONSTRAINT waitlist_email_key UNIQUE (email);


--
-- Name: waitlist waitlist_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.waitlist
    ADD CONSTRAINT waitlist_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: subscription pk_subscription; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.subscription
    ADD CONSTRAINT pk_subscription PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: buckets_analytics buckets_analytics_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets_analytics
    ADD CONSTRAINT buckets_analytics_pkey PRIMARY KEY (id);


--
-- Name: buckets buckets_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets
    ADD CONSTRAINT buckets_pkey PRIMARY KEY (id);


--
-- Name: buckets_vectors buckets_vectors_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets_vectors
    ADD CONSTRAINT buckets_vectors_pkey PRIMARY KEY (id);


--
-- Name: migrations migrations_name_key; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_name_key UNIQUE (name);


--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- Name: prefixes prefixes_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.prefixes
    ADD CONSTRAINT prefixes_pkey PRIMARY KEY (bucket_id, level, name);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_pkey PRIMARY KEY (id);


--
-- Name: s3_multipart_uploads s3_multipart_uploads_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_pkey PRIMARY KEY (id);


--
-- Name: vector_indexes vector_indexes_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.vector_indexes
    ADD CONSTRAINT vector_indexes_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_idempotency_key_key; Type: CONSTRAINT; Schema: supabase_migrations; Owner: -
--

ALTER TABLE ONLY supabase_migrations.schema_migrations
    ADD CONSTRAINT schema_migrations_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: supabase_migrations; Owner: -
--

ALTER TABLE ONLY supabase_migrations.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: audit_logs_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX audit_logs_instance_id_idx ON auth.audit_log_entries USING btree (instance_id);


--
-- Name: confirmation_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX confirmation_token_idx ON auth.users USING btree (confirmation_token) WHERE ((confirmation_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: email_change_token_current_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX email_change_token_current_idx ON auth.users USING btree (email_change_token_current) WHERE ((email_change_token_current)::text !~ '^[0-9 ]*$'::text);


--
-- Name: email_change_token_new_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX email_change_token_new_idx ON auth.users USING btree (email_change_token_new) WHERE ((email_change_token_new)::text !~ '^[0-9 ]*$'::text);


--
-- Name: factor_id_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX factor_id_created_at_idx ON auth.mfa_factors USING btree (user_id, created_at);


--
-- Name: flow_state_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX flow_state_created_at_idx ON auth.flow_state USING btree (created_at DESC);


--
-- Name: identities_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX identities_email_idx ON auth.identities USING btree (email text_pattern_ops);


--
-- Name: INDEX identities_email_idx; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON INDEX auth.identities_email_idx IS 'Auth: Ensures indexed queries on the email column';


--
-- Name: identities_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX identities_user_id_idx ON auth.identities USING btree (user_id);


--
-- Name: idx_auth_code; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_auth_code ON auth.flow_state USING btree (auth_code);


--
-- Name: idx_user_id_auth_method; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_user_id_auth_method ON auth.flow_state USING btree (user_id, authentication_method);


--
-- Name: mfa_challenge_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX mfa_challenge_created_at_idx ON auth.mfa_challenges USING btree (created_at DESC);


--
-- Name: mfa_factors_user_friendly_name_unique; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX mfa_factors_user_friendly_name_unique ON auth.mfa_factors USING btree (friendly_name, user_id) WHERE (TRIM(BOTH FROM friendly_name) <> ''::text);


--
-- Name: mfa_factors_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX mfa_factors_user_id_idx ON auth.mfa_factors USING btree (user_id);


--
-- Name: oauth_auth_pending_exp_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_auth_pending_exp_idx ON auth.oauth_authorizations USING btree (expires_at) WHERE (status = 'pending'::auth.oauth_authorization_status);


--
-- Name: oauth_clients_deleted_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_clients_deleted_at_idx ON auth.oauth_clients USING btree (deleted_at);


--
-- Name: oauth_consents_active_client_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_consents_active_client_idx ON auth.oauth_consents USING btree (client_id) WHERE (revoked_at IS NULL);


--
-- Name: oauth_consents_active_user_client_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_consents_active_user_client_idx ON auth.oauth_consents USING btree (user_id, client_id) WHERE (revoked_at IS NULL);


--
-- Name: oauth_consents_user_order_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_consents_user_order_idx ON auth.oauth_consents USING btree (user_id, granted_at DESC);


--
-- Name: one_time_tokens_relates_to_hash_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX one_time_tokens_relates_to_hash_idx ON auth.one_time_tokens USING hash (relates_to);


--
-- Name: one_time_tokens_token_hash_hash_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX one_time_tokens_token_hash_hash_idx ON auth.one_time_tokens USING hash (token_hash);


--
-- Name: one_time_tokens_user_id_token_type_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX one_time_tokens_user_id_token_type_key ON auth.one_time_tokens USING btree (user_id, token_type);


--
-- Name: reauthentication_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX reauthentication_token_idx ON auth.users USING btree (reauthentication_token) WHERE ((reauthentication_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: recovery_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX recovery_token_idx ON auth.users USING btree (recovery_token) WHERE ((recovery_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: refresh_tokens_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_instance_id_idx ON auth.refresh_tokens USING btree (instance_id);


--
-- Name: refresh_tokens_instance_id_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_instance_id_user_id_idx ON auth.refresh_tokens USING btree (instance_id, user_id);


--
-- Name: refresh_tokens_parent_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_parent_idx ON auth.refresh_tokens USING btree (parent);


--
-- Name: refresh_tokens_session_id_revoked_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_session_id_revoked_idx ON auth.refresh_tokens USING btree (session_id, revoked);


--
-- Name: refresh_tokens_updated_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_updated_at_idx ON auth.refresh_tokens USING btree (updated_at DESC);


--
-- Name: saml_providers_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_providers_sso_provider_id_idx ON auth.saml_providers USING btree (sso_provider_id);


--
-- Name: saml_relay_states_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_created_at_idx ON auth.saml_relay_states USING btree (created_at DESC);


--
-- Name: saml_relay_states_for_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_for_email_idx ON auth.saml_relay_states USING btree (for_email);


--
-- Name: saml_relay_states_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_sso_provider_id_idx ON auth.saml_relay_states USING btree (sso_provider_id);


--
-- Name: sessions_not_after_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_not_after_idx ON auth.sessions USING btree (not_after DESC);


--
-- Name: sessions_oauth_client_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_oauth_client_id_idx ON auth.sessions USING btree (oauth_client_id);


--
-- Name: sessions_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_user_id_idx ON auth.sessions USING btree (user_id);


--
-- Name: sso_domains_domain_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX sso_domains_domain_idx ON auth.sso_domains USING btree (lower(domain));


--
-- Name: sso_domains_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sso_domains_sso_provider_id_idx ON auth.sso_domains USING btree (sso_provider_id);


--
-- Name: sso_providers_resource_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX sso_providers_resource_id_idx ON auth.sso_providers USING btree (lower(resource_id));


--
-- Name: sso_providers_resource_id_pattern_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sso_providers_resource_id_pattern_idx ON auth.sso_providers USING btree (resource_id text_pattern_ops);


--
-- Name: unique_phone_factor_per_user; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX unique_phone_factor_per_user ON auth.mfa_factors USING btree (user_id, phone);


--
-- Name: user_id_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX user_id_created_at_idx ON auth.sessions USING btree (user_id, created_at);


--
-- Name: users_email_partial_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX users_email_partial_key ON auth.users USING btree (email) WHERE (is_sso_user = false);


--
-- Name: INDEX users_email_partial_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON INDEX auth.users_email_partial_key IS 'Auth: A partial unique index that applies only when is_sso_user is false';


--
-- Name: users_instance_id_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_instance_id_email_idx ON auth.users USING btree (instance_id, lower((email)::text));


--
-- Name: users_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_instance_id_idx ON auth.users USING btree (instance_id);


--
-- Name: users_is_anonymous_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_is_anonymous_idx ON auth.users USING btree (is_anonymous);


--
-- Name: idx_cookbook_folders_cookbook_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbook_folders_cookbook_id ON public.cookbook_folders USING btree (cookbook_id);


--
-- Name: idx_cookbook_folders_parent_folder_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbook_folders_parent_folder_id ON public.cookbook_folders USING btree (parent_folder_id);


--
-- Name: idx_cookbook_recipes_cookbook_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbook_recipes_cookbook_id ON public.cookbook_recipes USING btree (cookbook_id);


--
-- Name: idx_cookbook_recipes_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbook_recipes_recipe_id ON public.cookbook_recipes USING btree (recipe_id);


--
-- Name: idx_cookbook_shares_cookbook_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbook_shares_cookbook_id ON public.cookbook_shares USING btree (cookbook_id);


--
-- Name: idx_cookbook_shares_shared_with_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbook_shares_shared_with_user_id ON public.cookbook_shares USING btree (shared_with_user_id);


--
-- Name: idx_cookbooks_is_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbooks_is_public ON public.cookbooks USING btree (is_public);


--
-- Name: idx_cookbooks_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cookbooks_user_id ON public.cookbooks USING btree (user_id);


--
-- Name: idx_cooking_events_recipe_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cooking_events_recipe_time ON public.recipe_cooking_events USING btree (recipe_id, cooked_at DESC);


--
-- Name: INDEX idx_cooking_events_recipe_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_cooking_events_recipe_time IS 'Supports time-based queries for recipe cooking events. Enables "most cooked this week" queries.';


--
-- Name: idx_cooking_events_time_recipe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cooking_events_time_recipe ON public.recipe_cooking_events USING btree (cooked_at DESC, recipe_id);


--
-- Name: INDEX idx_cooking_events_time_recipe; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_cooking_events_time_recipe IS 'Supports trending recipe queries by time window. Optimizes aggregation queries.';


--
-- Name: idx_cooking_events_user_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cooking_events_user_time ON public.recipe_cooking_events USING btree (user_id, cooked_at DESC);


--
-- Name: INDEX idx_cooking_events_user_time; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_cooking_events_user_time IS 'Supports queries for user cooking history over time.';


--
-- Name: idx_extraction_jobs_source_urls; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extraction_jobs_source_urls ON public.extraction_jobs USING gin (source_urls);


--
-- Name: idx_extraction_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extraction_jobs_status ON public.extraction_jobs USING btree (status);


--
-- Name: idx_extraction_jobs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extraction_jobs_user_id ON public.extraction_jobs USING btree (user_id);


--
-- Name: idx_featured_recipes_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_featured_recipes_dates ON public.featured_recipes USING btree (start_date, end_date);


--
-- Name: idx_featured_recipes_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_featured_recipes_recipe_id ON public.featured_recipes USING btree (recipe_id);


--
-- Name: idx_featured_recipes_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_featured_recipes_type ON public.featured_recipes USING btree (featured_type);


--
-- Name: idx_folder_recipes_folder_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_folder_recipes_folder_id ON public.folder_recipes USING btree (folder_id);


--
-- Name: idx_folder_recipes_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_folder_recipes_recipe_id ON public.folder_recipes USING btree (recipe_id);


--
-- Name: idx_recipe_contributors_display_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_contributors_display_name ON public.recipe_contributors USING btree (display_name) WHERE (display_name IS NOT NULL);


--
-- Name: idx_recipe_contributors_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_contributors_recipe_id ON public.recipe_contributors USING btree (recipe_id);


--
-- Name: idx_recipe_contributors_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_recipe_contributors_unique ON public.recipe_contributors USING btree (recipe_id, COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::uuid), "order");


--
-- Name: idx_recipe_contributors_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_contributors_user_id ON public.recipe_contributors USING btree (user_id);


--
-- Name: idx_recipe_shares_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_shares_recipe_id ON public.recipe_shares USING btree (recipe_id);


--
-- Name: idx_recipe_shares_shared_with_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipe_shares_shared_with_user_id ON public.recipe_shares USING btree (shared_with_user_id);


--
-- Name: idx_recipes_average_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_average_rating ON public.recipes USING btree (average_rating DESC NULLS LAST);


--
-- Name: INDEX idx_recipes_average_rating; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_average_rating IS 'Supports efficient filtering and sorting of recipes by average rating. NULLS LAST ensures unrated recipes appear at the end.';


--
-- Name: idx_recipes_categories; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_categories ON public.recipes USING gin (categories);


--
-- Name: idx_recipes_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_created_at ON public.recipes USING btree (created_at DESC);


--
-- Name: idx_recipes_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_created_by ON public.recipes USING btree (created_by);


--
-- Name: idx_recipes_created_by_is_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_created_by_is_public ON public.recipes USING btree (created_by, is_public);


--
-- Name: INDEX idx_recipes_created_by_is_public; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_created_by_is_public IS 'Composite index for user-specific recipe queries';


--
-- Name: idx_recipes_description_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_description_search ON public.recipes USING gin (to_tsvector('english'::regconfig, COALESCE(description, ''::text)));


--
-- Name: idx_recipes_is_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_is_draft ON public.recipes USING btree (is_draft) WHERE (is_draft = false);


--
-- Name: idx_recipes_is_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_is_public ON public.recipes USING btree (is_public);


--
-- Name: INDEX idx_recipes_is_public; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_is_public IS 'Index for fast filtering of public recipes';


--
-- Name: idx_recipes_original_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_original_recipe_id ON public.recipes USING btree (original_recipe_id);


--
-- Name: idx_recipes_public_not_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_public_not_draft ON public.recipes USING btree (id) WHERE ((is_public = true) AND (is_draft = false));


--
-- Name: idx_recipes_public_sort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_public_sort ON public.recipes USING btree (is_public, created_at DESC);


--
-- Name: INDEX idx_recipes_public_sort; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_public_sort IS 'Composite index for efficient public recipes query with date sorting.';


--
-- Name: idx_recipes_search_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_search_vector ON public.recipes USING gin (search_vector);


--
-- Name: INDEX idx_recipes_search_vector; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_search_vector IS 'GIN index for fast full-text search queries';


--
-- Name: idx_recipes_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_tags ON public.recipes USING gin (tags);


--
-- Name: idx_recipes_tags_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_tags_rating ON public.recipes USING gin (tags) WHERE (average_rating >= 4.0);


--
-- Name: INDEX idx_recipes_tags_rating; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_tags_rating IS 'Partial index for tag-based searches filtered by high ratings (>= 4.0). Optimizes recommendation queries.';


--
-- Name: idx_recipes_title_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_title_search ON public.recipes USING gin (to_tsvector('english'::regconfig, (title)::text));


--
-- Name: idx_recipes_total_times_cooked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_total_times_cooked ON public.recipes USING btree (total_times_cooked DESC);


--
-- Name: INDEX idx_recipes_total_times_cooked; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_total_times_cooked IS 'Supports efficient sorting and filtering of recipes by cooking popularity (total_times_cooked). Enables "most popular" queries.';


--
-- Name: idx_recipes_user_sort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipes_user_sort ON public.recipes USING btree (created_by, created_at DESC);


--
-- Name: INDEX idx_recipes_user_sort; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_recipes_user_sort IS 'Composite index for efficient user recipes query with date sorting. Eliminates need for separate filter and sort operations.';


--
-- Name: idx_user_onboarding_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_onboarding_user_id ON public.user_onboarding USING btree (user_id);


--
-- Name: idx_user_preferences_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_preferences_user_id ON public.user_preferences USING btree (user_id);


--
-- Name: idx_user_recipe_data_batch; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_batch ON public.user_recipe_data USING btree (user_id, recipe_id);


--
-- Name: INDEX idx_user_recipe_data_batch; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.idx_user_recipe_data_batch IS 'Composite index for batch fetching user data for multiple recipes, eliminating N+1 query problem.';


--
-- Name: idx_user_recipe_data_extracted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_extracted ON public.user_recipe_data USING btree (user_id, created_at DESC) WHERE (was_extracted = true);


--
-- Name: idx_user_recipe_data_favorites; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_favorites ON public.user_recipe_data USING btree (user_id, created_at DESC) WHERE (is_favorite = true);


--
-- Name: idx_user_recipe_data_is_favorite; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_is_favorite ON public.user_recipe_data USING btree (is_favorite);


--
-- Name: idx_user_recipe_data_recipe_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_recipe_id ON public.user_recipe_data USING btree (recipe_id);


--
-- Name: idx_user_recipe_data_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_user_id ON public.user_recipe_data USING btree (user_id);


--
-- Name: idx_user_recipe_data_was_extracted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_recipe_data_was_extracted ON public.user_recipe_data USING btree (recipe_id, user_id) WHERE (was_extracted = true);


--
-- Name: idx_users_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_created_at ON public.users USING btree (created_at DESC);


--
-- Name: idx_users_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_search ON public.users USING gin (to_tsvector('english'::regconfig, (name)::text));


--
-- Name: idx_video_creators_platform; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_creators_platform ON public.video_creators USING btree (platform, platform_user_id);


--
-- Name: idx_video_sources_platform; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_sources_platform ON public.video_sources USING btree (platform, platform_video_id);


--
-- Name: idx_video_sources_recipe; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_video_sources_recipe ON public.video_sources USING btree (recipe_id);


--
-- Name: idx_waitlist_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_waitlist_created_at ON public.waitlist USING btree (created_at DESC);


--
-- Name: idx_waitlist_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_waitlist_email ON public.waitlist USING btree (email);


--
-- Name: idx_waitlist_utm_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_waitlist_utm_source ON public.waitlist USING btree (utm_source);


--
-- Name: ix_realtime_subscription_entity; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX ix_realtime_subscription_entity ON realtime.subscription USING btree (entity);


--
-- Name: messages_inserted_at_topic_index; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_inserted_at_topic_index ON ONLY realtime.messages USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: subscription_subscription_id_entity_filters_key; Type: INDEX; Schema: realtime; Owner: -
--

CREATE UNIQUE INDEX subscription_subscription_id_entity_filters_key ON realtime.subscription USING btree (subscription_id, entity, filters);


--
-- Name: bname; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX bname ON storage.buckets USING btree (name);


--
-- Name: bucketid_objname; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX bucketid_objname ON storage.objects USING btree (bucket_id, name);


--
-- Name: buckets_analytics_unique_name_idx; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX buckets_analytics_unique_name_idx ON storage.buckets_analytics USING btree (name) WHERE (deleted_at IS NULL);


--
-- Name: idx_multipart_uploads_list; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_multipart_uploads_list ON storage.s3_multipart_uploads USING btree (bucket_id, key, created_at);


--
-- Name: idx_name_bucket_level_unique; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX idx_name_bucket_level_unique ON storage.objects USING btree (name COLLATE "C", bucket_id, level);


--
-- Name: idx_objects_bucket_id_name; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_objects_bucket_id_name ON storage.objects USING btree (bucket_id, name COLLATE "C");


--
-- Name: idx_objects_lower_name; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_objects_lower_name ON storage.objects USING btree ((path_tokens[level]), lower(name) text_pattern_ops, bucket_id, level);


--
-- Name: idx_prefixes_lower_name; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_prefixes_lower_name ON storage.prefixes USING btree (bucket_id, level, ((string_to_array(name, '/'::text))[level]), lower(name) text_pattern_ops);


--
-- Name: name_prefix_search; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX name_prefix_search ON storage.objects USING btree (name text_pattern_ops);


--
-- Name: objects_bucket_id_level_idx; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX objects_bucket_id_level_idx ON storage.objects USING btree (bucket_id, level, name COLLATE "C");


--
-- Name: vector_indexes_name_bucket_id_idx; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX vector_indexes_name_bucket_id_idx ON storage.vector_indexes USING btree (name, bucket_id);


--
-- Name: recipes recipes_search_vector_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER recipes_search_vector_trigger BEFORE INSERT OR UPDATE ON public.recipes FOR EACH ROW EXECUTE FUNCTION public.recipes_search_vector_update();


--
-- Name: user_recipe_data trigger_update_recipe_cooked_count; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_recipe_cooked_count AFTER INSERT OR DELETE OR UPDATE OF times_cooked ON public.user_recipe_data FOR EACH ROW EXECUTE FUNCTION public.update_recipe_cooked_count();


--
-- Name: TRIGGER trigger_update_recipe_cooked_count ON user_recipe_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TRIGGER trigger_update_recipe_cooked_count ON public.user_recipe_data IS 'Automatically updates recipes.total_times_cooked when a user marks a recipe as cooked. Fires after INSERT, UPDATE, or DELETE on user_recipe_data.times_cooked.';


--
-- Name: cookbooks update_cookbooks_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_cookbooks_updated_at BEFORE UPDATE ON public.cookbooks FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: extraction_jobs update_extraction_jobs_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_extraction_jobs_updated_at BEFORE UPDATE ON public.extraction_jobs FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: recipes update_recipes_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_recipes_updated_at BEFORE UPDATE ON public.recipes FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_preferences update_user_preferences_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_recipe_data update_user_recipe_data_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_user_recipe_data_updated_at BEFORE UPDATE ON public.user_recipe_data FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: video_creators update_video_creators_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_video_creators_updated_at BEFORE UPDATE ON public.video_creators FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: video_sources update_video_sources_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_video_sources_updated_at BEFORE UPDATE ON public.video_sources FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: subscription tr_check_filters; Type: TRIGGER; Schema: realtime; Owner: -
--

CREATE TRIGGER tr_check_filters BEFORE INSERT OR UPDATE ON realtime.subscription FOR EACH ROW EXECUTE FUNCTION realtime.subscription_check_filters();


--
-- Name: buckets enforce_bucket_name_length_trigger; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER enforce_bucket_name_length_trigger BEFORE INSERT OR UPDATE OF name ON storage.buckets FOR EACH ROW EXECUTE FUNCTION storage.enforce_bucket_name_length();


--
-- Name: objects objects_delete_delete_prefix; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER objects_delete_delete_prefix AFTER DELETE ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.delete_prefix_hierarchy_trigger();


--
-- Name: objects objects_insert_create_prefix; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER objects_insert_create_prefix BEFORE INSERT ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.objects_insert_prefix_trigger();


--
-- Name: objects objects_update_create_prefix; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER objects_update_create_prefix BEFORE UPDATE ON storage.objects FOR EACH ROW WHEN (((new.name <> old.name) OR (new.bucket_id <> old.bucket_id))) EXECUTE FUNCTION storage.objects_update_prefix_trigger();


--
-- Name: prefixes prefixes_create_hierarchy; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER prefixes_create_hierarchy BEFORE INSERT ON storage.prefixes FOR EACH ROW WHEN ((pg_trigger_depth() < 1)) EXECUTE FUNCTION storage.prefixes_insert_trigger();


--
-- Name: prefixes prefixes_delete_hierarchy; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER prefixes_delete_hierarchy AFTER DELETE ON storage.prefixes FOR EACH ROW EXECUTE FUNCTION storage.delete_prefix_hierarchy_trigger();


--
-- Name: objects update_objects_updated_at; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.update_updated_at_column();


--
-- Name: identities identities_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: mfa_amr_claims mfa_amr_claims_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- Name: mfa_challenges mfa_challenges_auth_factor_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_auth_factor_id_fkey FOREIGN KEY (factor_id) REFERENCES auth.mfa_factors(id) ON DELETE CASCADE;


--
-- Name: mfa_factors mfa_factors_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: oauth_authorizations oauth_authorizations_client_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_client_id_fkey FOREIGN KEY (client_id) REFERENCES auth.oauth_clients(id) ON DELETE CASCADE;


--
-- Name: oauth_authorizations oauth_authorizations_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: oauth_consents oauth_consents_client_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_client_id_fkey FOREIGN KEY (client_id) REFERENCES auth.oauth_clients(id) ON DELETE CASCADE;


--
-- Name: oauth_consents oauth_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: one_time_tokens one_time_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: refresh_tokens refresh_tokens_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- Name: saml_providers saml_providers_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: saml_relay_states saml_relay_states_flow_state_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_flow_state_id_fkey FOREIGN KEY (flow_state_id) REFERENCES auth.flow_state(id) ON DELETE CASCADE;


--
-- Name: saml_relay_states saml_relay_states_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_oauth_client_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_oauth_client_id_fkey FOREIGN KEY (oauth_client_id) REFERENCES auth.oauth_clients(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: sso_domains sso_domains_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: cookbook_folders cookbook_folders_cookbook_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_folders
    ADD CONSTRAINT cookbook_folders_cookbook_id_fkey FOREIGN KEY (cookbook_id) REFERENCES public.cookbooks(id) ON DELETE CASCADE;


--
-- Name: cookbook_folders cookbook_folders_parent_folder_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_folders
    ADD CONSTRAINT cookbook_folders_parent_folder_id_fkey FOREIGN KEY (parent_folder_id) REFERENCES public.cookbook_folders(id) ON DELETE CASCADE;


--
-- Name: cookbook_recipes cookbook_recipes_cookbook_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_recipes
    ADD CONSTRAINT cookbook_recipes_cookbook_id_fkey FOREIGN KEY (cookbook_id) REFERENCES public.cookbooks(id) ON DELETE CASCADE;


--
-- Name: cookbook_recipes cookbook_recipes_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_recipes
    ADD CONSTRAINT cookbook_recipes_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: cookbook_shares cookbook_shares_cookbook_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_shares
    ADD CONSTRAINT cookbook_shares_cookbook_id_fkey FOREIGN KEY (cookbook_id) REFERENCES public.cookbooks(id) ON DELETE CASCADE;


--
-- Name: cookbook_shares cookbook_shares_shared_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_shares
    ADD CONSTRAINT cookbook_shares_shared_by_user_id_fkey FOREIGN KEY (shared_by_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: cookbook_shares cookbook_shares_shared_with_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbook_shares
    ADD CONSTRAINT cookbook_shares_shared_with_user_id_fkey FOREIGN KEY (shared_with_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: cookbooks cookbooks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cookbooks
    ADD CONSTRAINT cookbooks_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: extraction_jobs extraction_jobs_existing_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraction_jobs
    ADD CONSTRAINT extraction_jobs_existing_recipe_id_fkey FOREIGN KEY (existing_recipe_id) REFERENCES public.recipes(id) ON DELETE SET NULL;


--
-- Name: extraction_jobs extraction_jobs_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraction_jobs
    ADD CONSTRAINT extraction_jobs_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE SET NULL;


--
-- Name: extraction_jobs extraction_jobs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraction_jobs
    ADD CONSTRAINT extraction_jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: featured_recipes featured_recipes_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.featured_recipes
    ADD CONSTRAINT featured_recipes_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: recipe_cooking_events fk_recipe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_cooking_events
    ADD CONSTRAINT fk_recipe FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: recipe_cooking_events fk_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_cooking_events
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: folder_recipes folder_recipes_folder_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.folder_recipes
    ADD CONSTRAINT folder_recipes_folder_id_fkey FOREIGN KEY (folder_id) REFERENCES public.cookbook_folders(id) ON DELETE CASCADE;


--
-- Name: folder_recipes folder_recipes_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.folder_recipes
    ADD CONSTRAINT folder_recipes_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: recipe_contributors recipe_contributors_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_contributors
    ADD CONSTRAINT recipe_contributors_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: recipe_contributors recipe_contributors_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_contributors
    ADD CONSTRAINT recipe_contributors_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;


--
-- Name: recipe_cooking_events recipe_cooking_events_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_cooking_events
    ADD CONSTRAINT recipe_cooking_events_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: recipe_cooking_events recipe_cooking_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_cooking_events
    ADD CONSTRAINT recipe_cooking_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: recipe_shares recipe_shares_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_shares
    ADD CONSTRAINT recipe_shares_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: recipe_shares recipe_shares_shared_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_shares
    ADD CONSTRAINT recipe_shares_shared_by_user_id_fkey FOREIGN KEY (shared_by_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: recipe_shares recipe_shares_shared_with_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipe_shares
    ADD CONSTRAINT recipe_shares_shared_with_user_id_fkey FOREIGN KEY (shared_with_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: recipes recipes_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: recipes recipes_original_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_original_recipe_id_fkey FOREIGN KEY (original_recipe_id) REFERENCES public.recipes(id) ON DELETE SET NULL;


--
-- Name: user_onboarding user_onboarding_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_onboarding
    ADD CONSTRAINT user_onboarding_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: user_preferences user_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_preferences
    ADD CONSTRAINT user_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: user_recipe_data user_recipe_data_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_recipe_data
    ADD CONSTRAINT user_recipe_data_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: user_recipe_data user_recipe_data_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_recipe_data
    ADD CONSTRAINT user_recipe_data_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: users users_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: video_sources video_sources_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_sources
    ADD CONSTRAINT video_sources_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id) ON DELETE CASCADE;


--
-- Name: video_sources video_sources_video_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.video_sources
    ADD CONSTRAINT video_sources_video_creator_id_fkey FOREIGN KEY (video_creator_id) REFERENCES public.video_creators(id) ON DELETE SET NULL;


--
-- Name: objects objects_bucketId_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT "objects_bucketId_fkey" FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: prefixes prefixes_bucketId_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.prefixes
    ADD CONSTRAINT "prefixes_bucketId_fkey" FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads s3_multipart_uploads_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_upload_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES storage.s3_multipart_uploads(id) ON DELETE CASCADE;


--
-- Name: vector_indexes vector_indexes_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.vector_indexes
    ADD CONSTRAINT vector_indexes_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets_vectors(id);


--
-- Name: audit_log_entries; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.audit_log_entries ENABLE ROW LEVEL SECURITY;

--
-- Name: flow_state; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.flow_state ENABLE ROW LEVEL SECURITY;

--
-- Name: identities; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.identities ENABLE ROW LEVEL SECURITY;

--
-- Name: instances; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.instances ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_amr_claims; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_amr_claims ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_challenges; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_challenges ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_factors; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_factors ENABLE ROW LEVEL SECURITY;

--
-- Name: one_time_tokens; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.one_time_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: refresh_tokens; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.refresh_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: saml_providers; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.saml_providers ENABLE ROW LEVEL SECURITY;

--
-- Name: saml_relay_states; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.saml_relay_states ENABLE ROW LEVEL SECURITY;

--
-- Name: schema_migrations; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.schema_migrations ENABLE ROW LEVEL SECURITY;

--
-- Name: sessions; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: sso_domains; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sso_domains ENABLE ROW LEVEL SECURITY;

--
-- Name: sso_providers; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sso_providers ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

--
-- Name: recipes Collaborators can update shared recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Collaborators can update shared recipes" ON public.recipes FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.recipe_shares
  WHERE ((recipe_shares.recipe_id = recipes.id) AND (recipe_shares.shared_with_user_id = auth.uid()) AND ((recipe_shares.permission_level)::text = 'collaborate'::text)))));


--
-- Name: featured_recipes Everyone can view featured recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Everyone can view featured recipes" ON public.featured_recipes FOR SELECT USING (true);


--
-- Name: recipe_contributors Everyone can view recipe contributors; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Everyone can view recipe contributors" ON public.recipe_contributors FOR SELECT USING (true);


--
-- Name: users Profiles are viewable by everyone; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Profiles are viewable by everyone" ON public.users FOR SELECT USING (true);


--
-- Name: cookbooks Public cookbooks are viewable by everyone; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Public cookbooks are viewable by everyone" ON public.cookbooks FOR SELECT USING ((is_public = true));


--
-- Name: recipes Public recipes are viewable by everyone; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Public recipes are viewable by everyone" ON public.recipes FOR SELECT USING ((is_public = true));


--
-- Name: recipe_contributors System can manage recipe contributors; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "System can manage recipe contributors" ON public.recipe_contributors USING (true);


--
-- Name: video_creators System can manage video creators; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "System can manage video creators" ON public.video_creators USING (true);


--
-- Name: video_sources System can manage video sources; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "System can manage video sources" ON public.video_sources USING (true);


--
-- Name: users Users can create their own profile; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can create their own profile" ON public.users FOR INSERT WITH CHECK ((auth.uid() = id));


--
-- Name: cookbook_shares Users can delete their cookbook shares; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can delete their cookbook shares" ON public.cookbook_shares FOR DELETE USING ((auth.uid() = shared_by_user_id));


--
-- Name: recipes Users can delete their own recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can delete their own recipes" ON public.recipes FOR DELETE USING ((auth.uid() = created_by));


--
-- Name: recipe_shares Users can delete their shares; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can delete their shares" ON public.recipe_shares FOR DELETE USING ((auth.uid() = shared_by_user_id));


--
-- Name: recipe_cooking_events Users can insert own cooking events; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert own cooking events" ON public.recipe_cooking_events FOR INSERT WITH CHECK ((auth.uid() = user_id));


--
-- Name: POLICY "Users can insert own cooking events" ON recipe_cooking_events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON POLICY "Users can insert own cooking events" ON public.recipe_cooking_events IS 'Users can record their own cooking events.';


--
-- Name: user_onboarding Users can insert own onboarding; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert own onboarding" ON public.user_onboarding FOR INSERT WITH CHECK ((auth.uid() = user_id));


--
-- Name: user_preferences Users can insert own preferences; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert own preferences" ON public.user_preferences FOR INSERT WITH CHECK ((auth.uid() = user_id));


--
-- Name: recipes Users can insert their own recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can insert their own recipes" ON public.recipes FOR INSERT WITH CHECK ((auth.uid() = created_by));


--
-- Name: cookbook_folders Users can manage folders in their cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage folders in their cookbooks" ON public.cookbook_folders USING ((EXISTS ( SELECT 1
   FROM public.cookbooks
  WHERE ((cookbooks.id = cookbook_folders.cookbook_id) AND (cookbooks.user_id = auth.uid())))));


--
-- Name: cookbook_recipes Users can manage recipes in their cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage recipes in their cookbooks" ON public.cookbook_recipes USING ((EXISTS ( SELECT 1
   FROM public.cookbooks
  WHERE ((cookbooks.id = cookbook_recipes.cookbook_id) AND (cookbooks.user_id = auth.uid())))));


--
-- Name: folder_recipes Users can manage recipes in their folders; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage recipes in their folders" ON public.folder_recipes USING ((EXISTS ( SELECT 1
   FROM (public.cookbook_folders
     JOIN public.cookbooks ON ((cookbooks.id = cookbook_folders.cookbook_id)))
  WHERE ((cookbook_folders.id = folder_recipes.folder_id) AND (cookbooks.user_id = auth.uid())))));


--
-- Name: cookbooks Users can manage their own cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage their own cookbooks" ON public.cookbooks USING ((auth.uid() = user_id));


--
-- Name: extraction_jobs Users can manage their own extraction jobs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage their own extraction jobs" ON public.extraction_jobs USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: user_recipe_data Users can manage their own recipe data; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can manage their own recipe data" ON public.user_recipe_data USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: POLICY "Users can manage their own recipe data" ON user_recipe_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON POLICY "Users can manage their own recipe data" ON public.user_recipe_data IS 'Users can manage their own recipe data.';


--
-- Name: cookbook_shares Users can share their cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can share their cookbooks" ON public.cookbook_shares FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM public.cookbooks
  WHERE ((cookbooks.id = cookbook_shares.cookbook_id) AND (cookbooks.user_id = auth.uid())))));


--
-- Name: recipe_shares Users can share their recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can share their recipes" ON public.recipe_shares FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM public.recipes
  WHERE ((recipes.id = recipe_shares.recipe_id) AND (recipes.created_by = auth.uid())))));


--
-- Name: user_onboarding Users can update own onboarding; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can update own onboarding" ON public.user_onboarding FOR UPDATE USING ((auth.uid() = user_id));


--
-- Name: user_preferences Users can update own preferences; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can update own preferences" ON public.user_preferences FOR UPDATE USING ((auth.uid() = user_id));


--
-- Name: users Users can update their own profile; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can update their own profile" ON public.users FOR UPDATE USING ((auth.uid() = id));


--
-- Name: recipes Users can update their own recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can update their own recipes" ON public.recipes FOR UPDATE USING ((auth.uid() = created_by));


--
-- Name: recipe_cooking_events Users can view cooking events for public recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view cooking events for public recipes" ON public.recipe_cooking_events FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.recipes
  WHERE ((recipes.id = recipe_cooking_events.recipe_id) AND (recipes.is_public = true)))));


--
-- Name: POLICY "Users can view cooking events for public recipes" ON recipe_cooking_events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON POLICY "Users can view cooking events for public recipes" ON public.recipe_cooking_events IS 'Users can view aggregated cooking events for public recipes (enables trending queries)';


--
-- Name: recipe_cooking_events Users can view own cooking events; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own cooking events" ON public.recipe_cooking_events FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: POLICY "Users can view own cooking events" ON recipe_cooking_events; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON POLICY "Users can view own cooking events" ON public.recipe_cooking_events IS 'Users can view their own cooking history';


--
-- Name: user_onboarding Users can view own onboarding; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own onboarding" ON public.user_onboarding FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: user_preferences Users can view own preferences; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view own preferences" ON public.user_preferences FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: cookbooks Users can view shared cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view shared cookbooks" ON public.cookbooks FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.cookbook_shares
  WHERE ((cookbook_shares.cookbook_id = cookbooks.id) AND (cookbook_shares.shared_with_user_id = auth.uid())))));


--
-- Name: recipes Users can view shared recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view shared recipes" ON public.recipes FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.recipe_shares
  WHERE ((recipe_shares.recipe_id = recipes.id) AND (recipe_shares.shared_with_user_id = auth.uid())))));


--
-- Name: cookbook_shares Users can view shares for their cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view shares for their cookbooks" ON public.cookbook_shares FOR SELECT USING (((auth.uid() = shared_by_user_id) OR (auth.uid() = shared_with_user_id)));


--
-- Name: recipe_shares Users can view shares for their recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view shares for their recipes" ON public.recipe_shares FOR SELECT USING (((auth.uid() = shared_by_user_id) OR (auth.uid() = shared_with_user_id)));


--
-- Name: cookbooks Users can view their own cookbooks; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own cookbooks" ON public.cookbooks FOR SELECT USING ((auth.uid() = user_id));


--
-- Name: recipes Users can view their own recipes including drafts; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own recipes including drafts" ON public.recipes FOR SELECT USING ((created_by = auth.uid()));


--
-- Name: video_creators Video creators are public; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Video creators are public" ON public.video_creators FOR SELECT USING (true);


--
-- Name: video_sources Video sources are public; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Video sources are public" ON public.video_sources FOR SELECT USING (true);


--
-- Name: recipes View public non-draft recipes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "View public non-draft recipes" ON public.recipes FOR SELECT USING (((is_public = true) AND (is_draft = false)));


--
-- Name: cookbook_folders; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cookbook_folders ENABLE ROW LEVEL SECURITY;

--
-- Name: cookbook_recipes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cookbook_recipes ENABLE ROW LEVEL SECURITY;

--
-- Name: cookbook_shares; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cookbook_shares ENABLE ROW LEVEL SECURITY;

--
-- Name: cookbooks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cookbooks ENABLE ROW LEVEL SECURITY;

--
-- Name: extraction_jobs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.extraction_jobs ENABLE ROW LEVEL SECURITY;

--
-- Name: featured_recipes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.featured_recipes ENABLE ROW LEVEL SECURITY;

--
-- Name: folder_recipes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.folder_recipes ENABLE ROW LEVEL SECURITY;

--
-- Name: recipe_contributors; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.recipe_contributors ENABLE ROW LEVEL SECURITY;

--
-- Name: recipe_cooking_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.recipe_cooking_events ENABLE ROW LEVEL SECURITY;

--
-- Name: recipe_shares; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.recipe_shares ENABLE ROW LEVEL SECURITY;

--
-- Name: recipes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;

--
-- Name: user_onboarding; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_onboarding ENABLE ROW LEVEL SECURITY;

--
-- Name: user_preferences; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

--
-- Name: user_recipe_data; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_recipe_data ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

--
-- Name: video_creators; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.video_creators ENABLE ROW LEVEL SECURITY;

--
-- Name: video_sources; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.video_sources ENABLE ROW LEVEL SECURITY;

--
-- Name: waitlist; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.waitlist ENABLE ROW LEVEL SECURITY;

--
-- Name: messages; Type: ROW SECURITY; Schema: realtime; Owner: -
--

ALTER TABLE realtime.messages ENABLE ROW LEVEL SECURITY;

--
-- Name: objects Cooking event images are publicly readable; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Cooking event images are publicly readable" ON storage.objects FOR SELECT USING ((bucket_id = 'cooking-events'::text));


--
-- Name: objects Recipe images are publicly readable; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Recipe images are publicly readable" ON storage.objects FOR SELECT USING ((bucket_id = 'recipe-images'::text));


--
-- Name: objects Users can delete their own cooking event images; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Users can delete their own cooking event images" ON storage.objects FOR DELETE TO authenticated USING (((bucket_id = 'cooking-events'::text) AND ((auth.uid())::text = (storage.foldername(name))[1])));


--
-- Name: objects Users can delete their own recipe images; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Users can delete their own recipe images" ON storage.objects FOR DELETE TO authenticated USING (((bucket_id = 'recipe-images'::text) AND ((auth.uid())::text = (storage.foldername(name))[1])));


--
-- Name: objects Users can update their own cooking event images; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Users can update their own cooking event images" ON storage.objects FOR UPDATE TO authenticated USING (((bucket_id = 'cooking-events'::text) AND ((auth.uid())::text = (storage.foldername(name))[1])));


--
-- Name: objects Users can update their own recipe images; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Users can update their own recipe images" ON storage.objects FOR UPDATE TO authenticated USING (((bucket_id = 'recipe-images'::text) AND ((auth.uid())::text = (storage.foldername(name))[1])));


--
-- Name: objects Users can upload cooking event images; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Users can upload cooking event images" ON storage.objects FOR INSERT TO authenticated WITH CHECK (((bucket_id = 'cooking-events'::text) AND ((auth.uid())::text = (storage.foldername(name))[1])));


--
-- Name: objects Users can upload recipe images; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Users can upload recipe images" ON storage.objects FOR INSERT TO authenticated WITH CHECK (((bucket_id = 'recipe-images'::text) AND ((auth.uid())::text = (storage.foldername(name))[1])));


--
-- Name: buckets; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

--
-- Name: buckets_analytics; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets_analytics ENABLE ROW LEVEL SECURITY;

--
-- Name: buckets_vectors; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets_vectors ENABLE ROW LEVEL SECURITY;

--
-- Name: migrations; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.migrations ENABLE ROW LEVEL SECURITY;

--
-- Name: objects; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

--
-- Name: prefixes; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.prefixes ENABLE ROW LEVEL SECURITY;

--
-- Name: s3_multipart_uploads; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.s3_multipart_uploads ENABLE ROW LEVEL SECURITY;

--
-- Name: s3_multipart_uploads_parts; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.s3_multipart_uploads_parts ENABLE ROW LEVEL SECURITY;

--
-- Name: vector_indexes; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.vector_indexes ENABLE ROW LEVEL SECURITY;

--
-- Name: supabase_realtime; Type: PUBLICATION; Schema: -; Owner: -
--

CREATE PUBLICATION supabase_realtime WITH (publish = 'insert, update, delete, truncate');


--
-- Name: issue_graphql_placeholder; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_graphql_placeholder ON sql_drop
         WHEN TAG IN ('DROP EXTENSION')
   EXECUTE FUNCTION extensions.set_graphql_placeholder();


--
-- Name: issue_pg_cron_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_cron_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_cron_access();


--
-- Name: issue_pg_graphql_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_graphql_access ON ddl_command_end
         WHEN TAG IN ('CREATE FUNCTION')
   EXECUTE FUNCTION extensions.grant_pg_graphql_access();


--
-- Name: issue_pg_net_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_net_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_net_access();


--
-- Name: pgrst_ddl_watch; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER pgrst_ddl_watch ON ddl_command_end
   EXECUTE FUNCTION extensions.pgrst_ddl_watch();


--
-- Name: pgrst_drop_watch; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER pgrst_drop_watch ON sql_drop
   EXECUTE FUNCTION extensions.pgrst_drop_watch();


--
-- PostgreSQL database dump complete
--

\unrestrict SNgc50alAw1GvG2FscR6NdlKLKXgc0M8dajlJTgU87a9VbhyiMR0Yt6ktvI8VPP

