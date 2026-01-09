-- Migration: Seed initial categories with translations
-- Description: Inserts the 17 dish-type categories with English and French translations
-- Run this migration AFTER 015_create_categories_table.sql

-- Insert categories with their AI descriptions
INSERT INTO public.categories (slug, description, display_order, icon) VALUES
    ('main-dishes', 'Main course dishes, entrees, primary meals', 1, NULL),
    ('soups', 'Soups, stews, broths, chowders', 2, NULL),
    ('salads', 'Salads, slaws, fresh vegetable dishes', 3, NULL),
    ('pasta-noodles', 'Pasta dishes, noodle dishes, ramen', 4, NULL),
    ('sandwiches', 'Sandwiches, wraps, burgers, tacos', 5, NULL),
    ('appetizers', 'Starters, small plates, finger foods', 6, NULL),
    ('apero', 'Aperitif snacks, charcuterie, cheese boards', 7, NULL),
    ('desserts', 'Sweet treats, cakes, pies, ice cream', 8, NULL),
    ('baked-goods', 'Breads, muffins, cookies, pastries', 9, NULL),
    ('beverages', 'Non-alcoholic drinks, smoothies, juices', 10, NULL),
    ('cocktails', 'Alcoholic drinks, mixed drinks, wines', 11, NULL),
    ('breakfast', 'Morning meals, eggs, pancakes, cereals', 12, NULL),
    ('sides', 'Side dishes, vegetables, rice, potatoes', 13, NULL),
    ('sauces-dips', 'Sauces, dressings, condiments, dips', 14, NULL),
    ('snacks', 'Light bites, chips, nuts, popcorn', 15, NULL),
    ('grilled', 'BBQ, grilled meats, kebabs', 16, NULL),
    ('bowls-grains', 'Buddha bowls, grain bowls, quinoa dishes', 17, NULL)
ON CONFLICT (slug) DO NOTHING;

-- Insert English translations
INSERT INTO public.category_translations (category_id, locale, name)
SELECT id, 'en', 'Main Dishes' FROM public.categories WHERE slug = 'main-dishes'
UNION ALL SELECT id, 'en', 'Soups' FROM public.categories WHERE slug = 'soups'
UNION ALL SELECT id, 'en', 'Salads' FROM public.categories WHERE slug = 'salads'
UNION ALL SELECT id, 'en', 'Pasta & Noodles' FROM public.categories WHERE slug = 'pasta-noodles'
UNION ALL SELECT id, 'en', 'Sandwiches' FROM public.categories WHERE slug = 'sandwiches'
UNION ALL SELECT id, 'en', 'Appetizers' FROM public.categories WHERE slug = 'appetizers'
UNION ALL SELECT id, 'en', 'Apéro' FROM public.categories WHERE slug = 'apero'
UNION ALL SELECT id, 'en', 'Desserts' FROM public.categories WHERE slug = 'desserts'
UNION ALL SELECT id, 'en', 'Baked Goods' FROM public.categories WHERE slug = 'baked-goods'
UNION ALL SELECT id, 'en', 'Beverages' FROM public.categories WHERE slug = 'beverages'
UNION ALL SELECT id, 'en', 'Cocktails' FROM public.categories WHERE slug = 'cocktails'
UNION ALL SELECT id, 'en', 'Breakfast' FROM public.categories WHERE slug = 'breakfast'
UNION ALL SELECT id, 'en', 'Sides' FROM public.categories WHERE slug = 'sides'
UNION ALL SELECT id, 'en', 'Sauces & Dips' FROM public.categories WHERE slug = 'sauces-dips'
UNION ALL SELECT id, 'en', 'Snacks' FROM public.categories WHERE slug = 'snacks'
UNION ALL SELECT id, 'en', 'Grilled' FROM public.categories WHERE slug = 'grilled'
UNION ALL SELECT id, 'en', 'Bowls & Grains' FROM public.categories WHERE slug = 'bowls-grains'
ON CONFLICT (category_id, locale) DO NOTHING;

-- Insert French translations
INSERT INTO public.category_translations (category_id, locale, name)
SELECT id, 'fr', 'Plats Principaux' FROM public.categories WHERE slug = 'main-dishes'
UNION ALL SELECT id, 'fr', 'Soupes' FROM public.categories WHERE slug = 'soups'
UNION ALL SELECT id, 'fr', 'Salades' FROM public.categories WHERE slug = 'salads'
UNION ALL SELECT id, 'fr', 'Pâtes & Nouilles' FROM public.categories WHERE slug = 'pasta-noodles'
UNION ALL SELECT id, 'fr', 'Sandwichs' FROM public.categories WHERE slug = 'sandwiches'
UNION ALL SELECT id, 'fr', 'Entrées' FROM public.categories WHERE slug = 'appetizers'
UNION ALL SELECT id, 'fr', 'Apéro' FROM public.categories WHERE slug = 'apero'
UNION ALL SELECT id, 'fr', 'Desserts' FROM public.categories WHERE slug = 'desserts'
UNION ALL SELECT id, 'fr', 'Pâtisseries' FROM public.categories WHERE slug = 'baked-goods'
UNION ALL SELECT id, 'fr', 'Boissons' FROM public.categories WHERE slug = 'beverages'
UNION ALL SELECT id, 'fr', 'Cocktails' FROM public.categories WHERE slug = 'cocktails'
UNION ALL SELECT id, 'fr', 'Petit-déjeuner' FROM public.categories WHERE slug = 'breakfast'
UNION ALL SELECT id, 'fr', 'Accompagnements' FROM public.categories WHERE slug = 'sides'
UNION ALL SELECT id, 'fr', 'Sauces & Dips' FROM public.categories WHERE slug = 'sauces-dips'
UNION ALL SELECT id, 'fr', 'Snacks' FROM public.categories WHERE slug = 'snacks'
UNION ALL SELECT id, 'fr', 'Grillades' FROM public.categories WHERE slug = 'grilled'
UNION ALL SELECT id, 'fr', 'Bowls & Céréales' FROM public.categories WHERE slug = 'bowls-grains'
ON CONFLICT (category_id, locale) DO NOTHING;
