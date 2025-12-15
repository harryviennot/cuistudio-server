# LLM Recipe Extraction Comparison (Production Prompt)

**Generated**: 2025-12-15 15:35:01

Using actual production prompt from `openai_service.py`

## Summary Table (All Images)

| Image | Model | Latency | TTFT | Cost | Ingredients | Steps |
|-------|-------|---------|------|------|-------------|-------|
| IMG_5357.HEIC | gemini-2.5-flash-lite | 4.92s | 0.84s | $0.0004 | 10 | 5 |
| IMG_5357.HEIC | gemini-2.0-flash | 6.38s | 0.63s | $0.0005 | 10 | 5 |
| IMG_5357.HEIC | gemini-2.0-flash-lite | 9.33s | 3.75s | $0.0004 | 10 | 5 |
| IMG_5357.HEIC | gpt-4o | 11.18s | 0.70s | $0.0086 | 10 | 5 |
| IMG_5357.HEIC | gpt-4o-mini | 18.91s | 0.73s | $0.0005 | 10 | 5 |
| IMG_5357.HEIC | gemini-2.5-flash | FAILED | - | - | - | - |
| IMG_5357.HEIC | claude-3-5-haiku-latest | FAILED | - | - | - | - |
| IMG_5362.HEIC | gemini-2.5-flash-lite | 2.28s | 0.68s | $0.0004 | 9 | 7 |
| IMG_5362.HEIC | gemini-2.0-flash | 5.69s | 0.45s | $0.0005 | 10 | 3 |
| IMG_5362.HEIC | gemini-2.0-flash-lite | 6.97s | 0.98s | $0.0004 | 10 | 7 |
| IMG_5362.HEIC | gpt-4o | 11.09s | 1.50s | $0.0089 | 10 | 4 |
| IMG_5362.HEIC | gpt-4o-mini | 18.64s | 0.54s | $0.0006 | 10 | 9 |
| IMG_5362.HEIC | gemini-2.5-flash | FAILED | - | - | - | - |
| IMG_5362.HEIC | claude-3-5-haiku-latest | FAILED | - | - | - | - |
| IMG_5363.HEIC | gemini-2.0-flash-lite | 6.83s | 0.55s | $0.0004 | 20 | 5 |
| IMG_5363.HEIC | gemini-2.0-flash | 7.57s | 0.37s | $0.0007 | 19 | 4 |
| IMG_5363.HEIC | gemini-2.5-flash-lite | 8.26s | 0.92s | $0.0006 | 19 | 6 |
| IMG_5363.HEIC | gpt-4o | 15.45s | 0.68s | $0.0135 | 18 | 5 |
| IMG_5363.HEIC | gpt-4o-mini | 26.69s | 0.54s | $0.0008 | 17 | 6 |
| IMG_5363.HEIC | gemini-2.5-flash | FAILED | - | - | - | - |
| IMG_5363.HEIC | claude-3-5-haiku-latest | FAILED | - | - | - | - |
| IMG_5365.HEIC | gemini-2.5-flash-lite | 2.84s | 0.68s | $0.0005 | 12 | 5 |
| IMG_5365.HEIC | gemini-2.0-flash | 7.00s | 0.48s | $0.0006 | 12 | 5 |
| IMG_5365.HEIC | gemini-2.0-flash-lite | 8.41s | 1.41s | $0.0005 | 12 | 5 |
| IMG_5365.HEIC | claude-3-5-haiku-latest | 15.02s | 0.87s | $0.0059 | 10 | 7 |
| IMG_5365.HEIC | gpt-4o-mini | 15.98s | 0.65s | $0.0005 | 9 | 5 |
| IMG_5365.HEIC | gpt-4o | 17.33s | 0.82s | $0.0104 | 10 | 6 |
| IMG_5365.HEIC | gemini-2.5-flash | 34.96s | 29.65s | $0.0010 | 12 | 6 |
| IMG_5482.HEIC | gemini-2.5-flash-lite | 4.07s | 0.72s | $0.0007 | 16 | 9 |
| IMG_5482.HEIC | gemini-2.0-flash-lite | 11.32s | 2.46s | $0.0006 | 15 | 7 |
| IMG_5482.HEIC | gemini-2.0-flash | 11.52s | 0.73s | $0.0008 | 16 | 8 |
| IMG_5482.HEIC | gemini-2.5-flash | 21.51s | 13.35s | $0.0014 | 15 | 13 |
| IMG_5482.HEIC | gpt-4o-mini | 22.70s | 0.84s | $0.0009 | 14 | 7 |
| IMG_5482.HEIC | gpt-4o | 23.74s | 0.79s | $0.0141 | 15 | 7 |
| IMG_5482.HEIC | claude-3-5-haiku-latest | FAILED | - | - | - | - |
| IMG_5485.HEIC | gemini-2.5-flash-lite | 6.75s | 0.63s | $0.0005 | 11 | 6 |
| IMG_5485.HEIC | gemini-2.0-flash | 7.25s | 0.55s | $0.0007 | 11 | 4 |
| IMG_5485.HEIC | gemini-2.0-flash-lite | 8.57s | 2.07s | $0.0005 | 11 | 4 |
| IMG_5485.HEIC | gpt-4o | 15.36s | 0.87s | $0.0127 | 11 | 6 |
| IMG_5485.HEIC | gpt-4o-mini | 26.79s | 0.55s | $0.0008 | 11 | 7 |
| IMG_5485.HEIC | gemini-2.5-flash | FAILED | - | - | - | - |
| IMG_5485.HEIC | claude-3-5-haiku-latest | FAILED | - | - | - | - |

## Model Averages

| Model | Avg Latency | Avg Cost | Avg Ingredients | Avg Steps |
|-------|-------------|----------|-----------------|-----------|
| gemini-2.5-flash-lite | 4.85s | $0.0005 | 12.8 | 6.3 |
| gemini-2.0-flash | 7.57s | $0.0006 | 13.0 | 4.8 |
| gemini-2.0-flash-lite | 8.57s | $0.0005 | 13.0 | 5.5 |
| claude-3-5-haiku-latest | 15.02s | $0.0059 | 10.0 | 7.0 |
| gpt-4o | 15.69s | $0.0114 | 12.3 | 5.5 |
| gpt-4o-mini | 21.62s | $0.0007 | 11.8 | 6.5 |
| gemini-2.5-flash | 28.23s | $0.0012 | 13.5 | 9.5 |

---

## Full Recipe Comparison by Image

### IMG_5357.HEIC

#### gemini-2.5-flash-lite

**Provider**: Google | **Latency**: 4.92s | **Cost**: $0.0004

**Title**: Velouté de carottes au cumin

**Description**: A creamy carrot soup with cumin, topped with seared scallops.

**Servings**: 6 | **Difficulty**: easy | **Prep**: 10 min | **Cook**: 32 min | **Total**: 42 min

**Ingredients:**


*For the soup*
- 12.0 carrots (peeled and sliced)

*For the garnish*
- 6.0 scallops (cleaned)

*For the soup*
- 50.0 g butter
- 1.0 tsp olive oil
- 1.0 L vegetable broth
- 0.5 L water
- 3.0 tbsp fresh cream
- 1.0 tsp ground cumin

*To taste*
- fleur de sel (to taste)
- pepper (to taste)

**Instructions:**


*For the soup*
1. **Sauté Carrots**: In a saucepan, heat the oil and butter. Sauté the sliced carrots for a few minutes. _(~5 min)_
2. **Cook Soup Base**: Add the water and vegetable broth. Let it simmer over low heat for 20 to 25 minutes. _(~25 min)_
3. **Blend and Season**: Blend the soup until smooth. Stir in the cumin, salt, pepper, and cream. Keep warm. _(~5 min)_

*For the garnish*
4. **Sear Scallops**: Quickly sear the scallops. _(~2 min)_

*Serving*
5. **Serve**: In each plate, place a seared scallop and pour the hot velouté over it. _(~1 min)_

**Tags**: carrot, cumin, scallop, velouté, soup | **Categories**: Soup, Appetizer

---

#### gemini-2.0-flash

**Provider**: Google | **Latency**: 6.38s | **Cost**: $0.0005

**Title**: Velouté de carottes au cumin

**Description**: Creamy carrot soup with cumin

**Servings**: 6 | **Difficulty**: easy | **Prep**: 10 min | **Cook**: 25 min | **Total**: 35 min

**Ingredients:**

- 12.0 carrots
- 6.0 scallops
- 50.0 g butter
- 1.0 tablespoon olive oil
- 1.0 l vegetable broth
- 50.0 cl water
- 3.0 tablespoon fresh cream (3 to 4)
- 1.0 tablespoon ground cumin
- fleur de sel (to taste)
- pepper (to taste)

**Instructions:**

1. **Sauté carrots**: In a saucepan, heat the oil and butter, let the carrot slices brown for a few minutes before adding the water and broth. _(~5 min)_
2. **Simmer**: Let it cook over low heat for 20 to 25 minutes. _(~23 min)_
3. **Blend and season**: Blend and add the cumin, salt, pepper and cream. Keep warm. _(~5 min)_
4. **Grill scallops**: Quickly grill the scallops. _(~3 min)_
5. **Serve**: In each plate, place a scallop and pour the hot velouté over it. _(~2 min)_

**Tags**: soup, carrot, cumin, scallops | **Categories**: soup

---

#### gemini-2.0-flash-lite

**Provider**: Google | **Latency**: 9.33s | **Cost**: $0.0004

**Title**: Velouté de carottes au cumin (Carrot and Cumin Soup)

**Description**: A creamy and flavorful carrot soup with cumin, served with seared scallops.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 10 min | **Cook**: 25 min | **Total**: 35 min

**Ingredients:**


*For the soup*
- 12.0 carrots

*For the scallops*
- 6.0 sea scallops (large)

*For the soup*
- 50.0 g butter
- 1.0 Cc. a S. olive oil
- 1.0 L vegetable broth
- 50.0 CL water
- 3.0 to 4 heavy cream (Cc. a S.)
- 1.0 Cc. a S. ground cumin

*To taste*
- fleur de sel
- black pepper

**Instructions:**


*For the soup*
1. **Sauté Carrots**: In a saucepan, heat the oil and butter. Sauté the carrot rounds for a few minutes before adding the water and broth. _(~5 min)_
2. **Simmer Soup**: Simmer over low heat for 20-25 minutes. _(~23 min)_
3. **Blend and Season**: Blend the soup, then add the cumin, salt, pepper, and cream. Keep warm. _(~5 min)_

*For the scallops*
4. **Sear Scallops**: Quickly grill the scallops. _(~2 min)_

*For the soup*
5. **Serve**: In each plate, place a scallop and pour the warm soup over it. _(~2 min)_

**Tags**: soup, carrots, cumin, scallops | **Categories**: soups

---

#### gpt-4o

**Provider**: OpenAI | **Latency**: 11.18s | **Cost**: $0.0086

**Title**: Velouté de Carottes au Cumin

**Description**: A creamy carrot soup flavored with cumin, served with grilled scallops.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 10 min | **Cook**: 25 min | **Total**: 35 min

**Ingredients:**


*For the soup*
- 12.0 carrots (sliced)
- 50.0 g butter
- 1.0 tablespoon olive oil
- 1.0 liter vegetable broth
- 500.0 ml water
- 3.0 tablespoons heavy cream
- 1.0 teaspoon ground cumin

*To taste*
- fleur de sel (to taste)
- pepper (to taste)

*For the garnish*
- 6.0 scallops (large)

**Instructions:**


*For the soup*
1. **Prepare the Soup Base**: In a saucepan, heat the olive oil and butter. Sauté the sliced carrots for a few minutes. _(~10 min)_
2. **Cook the Soup**: Add the water and vegetable broth to the saucepan. Simmer on low heat for 20 to 25 minutes. _(~25 min)_
3. **Blend and Season**: Blend the soup until smooth. Stir in the cumin, salt, pepper, and cream. Keep warm. _(~5 min)_

*For the garnish*
4. **Grill the Scallops**: Quickly grill the scallops until cooked through. _(~5 min)_
5. **Serve**: Place a scallop in each bowl and pour the hot velouté over it. _(~5 min)_

**Tags**: soup, French, carrot, scallops | **Categories**: Soup

---

#### gpt-4o-mini

**Provider**: OpenAI | **Latency**: 18.91s | **Cost**: $0.0005

**Title**: Velouté de Carottes au Cumin

**Description**: A creamy carrot soup flavored with cumin, served with scallops.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 10 min | **Cook**: 30 min | **Total**: 40 min

**Ingredients:**


*For the soup*
- 12.0 pieces carrots (sliced)

*For the garnish*
- 6.0 pieces scallops (grilled)

*For the soup*
- 50.0 grams butter (for cooking)
- 1.0 tablespoon olive oil (for cooking)
- 1.0 liter vegetable broth (for soup base)
- 50.0 centiliters water (for soup)
- 30.0 centiliters fresh cream (for finishing)
- 1.0 teaspoon ground cumin (for flavor)

*To taste*
- fleur de sel (to taste)
- pepper (to taste)

**Instructions:**


*For the soup*
1. **Prepare the ingredients**: In a pot, heat the olive oil and butter. Add the sliced carrots and sauté for a few minutes. _(~10 min)_
2. **Cook the soup**: Add the water and vegetable broth. Let it simmer on low heat for 20 to 25 minutes. _(~25 min)_
3. **Blend the soup**: Blend the soup until smooth, then add the cumin, salt, pepper, and fresh cream. Keep warm. _(~5 min)_

*For the garnish*
4. **Grill the scallops**: Quickly grill the scallops until cooked. _(~5 min)_
5. **Serve the dish**: In each plate, place a scallop and pour the warm velouté over it. _(~2 min)_

**Tags**: soup, carrot, scallops | **Categories**: soup, appetizer

---

#### gemini-2.5-flash

**Provider**: Google | **Latency**: 7.91s | **Cost**: $0.0000

**Error**: 

---

#### claude-3-5-haiku-latest

**Provider**: Anthropic | **Latency**: 10.66s | **Cost**: $0.0000

**Error**: Expecting value: line 1 column 1 (char 0)

---

### IMG_5362.HEIC

#### gemini-2.5-flash-lite

**Provider**: Google | **Latency**: 2.28s | **Cost**: $0.0004

**Title**: Rice Salad

**Description**: A delicious homemade rice salad that's better than store-bought. Best eaten at room temperature.

**Servings**: 4 | **Difficulty**: easy | **Prep**: 15 min | **Cook**: 20 min | **Total**: 35 min

**Ingredients:**

- 250.0 g mixed long grain and wild rice
- 200.0 g roasted red peppers from a jar
- 1.0 fresh red chilli
- a few sprigs fresh basil
- a few sprigs fresh mint
- a few sprigs fresh flat-leaf parsley
- 1.0 lemon
- 4.0 tablespoons lemon dressing (see page 107)

*To taste*
- to taste sea salt and freshly ground black pepper

**Instructions:**

1. **Boil Rice**: Bring a large pan of salted water to the boil. Add the rice and cook it according to the packet instructions. _(~15 min)_
2. **Cool Rice**: Once cooked, drain the rice in a sieve and spread it out on a tray to help it cool down quickly. _(~5 min)_
3. **Prepare Herbs and Chilli**: Meanwhile, pick all the herb leaves off the stalks. Finely chop the peppers. Halve, deseed and finely chop your chilli. _(~5 min)_
4. **Prepare Lemon Dressing**: Make your lemon dressing (see page 107). _(~5 min)_
5. **Combine Ingredients**: Put your cooled rice into a big serving bowl. Finely chop your herb leaves and add them to the bowl, together with the peppers and chilli. _(~2 min)_
6. **Add Lemon and Dressing**: Zest over your lemon, add the dressing and mix well. _(~2 min)_
7. **Season and Serve**: Taste, add salt and pepper if you think it needs it, and serve. _(~1 min)_

**Tags**: rice, salad, vegetarian, summer | **Categories**: Salads, Side Dishes

---

#### gemini-2.0-flash

**Provider**: Google | **Latency**: 5.69s | **Cost**: $0.0005

**Title**: Rice Salad

**Description**: A homemade rice salad recipe that encourages experimentation with different rice grains and fresh herbs, offering a flavorful alternative to pre-packaged options.

**Servings**: 4 | **Difficulty**: easy | **Prep**: 20 min | **Cook**: 25 min | **Total**: 45 min

**Ingredients:**

- sea salt (to taste)
- freshly ground black pepper (to taste)
- 200.0 g roasted red peppers (from a jar)
- 250.0 g mixed long grain and wild rice
- 1.0 fresh red chilli
- sprigs fresh basil (a few)
- sprigs fresh mint (a few)
- sprigs fresh flat-leaf parsley (a few)
- 1.0 lemon
- 4.0 tablespoons lemon dressing (see page 107)

**Instructions:**

1. **Cook the rice**: Bring a large pan of salted water to the boil. Add the rice and cook it according to the packet instructions. Once cooked, drain the rice in a sieve and spread it out on a tray to help it cool down quickly. _(~25 min)_
2. **Prepare the ingredients**: Meanwhile, pick all the herb leaves off the stalks. Finely chop the peppers. Halve, deseed and finely chop your chilli. Make your lemon dressing. _(~15 min)_
3. **Combine and season**: Put your cooled rice into a big serving bowl. Finely chop your herb leaves and add them to the bowl, together with the peppers and chilli. Zest over your lemon, add the dressing and mix well. Taste, add salt and pepper if you think it needs it, and serve. _(~5 min)_

**Tags**: salad, rice, vegetarian, healthy | **Categories**: salads

---

#### gemini-2.0-flash-lite

**Provider**: Google | **Latency**: 6.97s | **Cost**: $0.0004

**Title**: Rice Salad

**Description**: A refreshing rice salad that's better than store-bought. Best served at room temperature.

**Servings**: 4 | **Difficulty**: easy | **Prep**: 15 min | **Cook**: 20 min | **Total**: 35 min

**Ingredients:**

- sea salt
- freshly ground black pepper
- 200.0 g roasted red peppers from a jar
- 250.0 g mixed long grain and wild rice
- 1.0 fresh red chilli
- sprigs fresh basil
- 1.0 lemon
- sprigs fresh mint
- 4.0 tablespoons lemon dressing (see page 107)
- sprigs fresh flat-leaf parsley

**Instructions:**

1. **Cook the rice**: Bring a large pan of salted water to the boil. Add the rice and cook it according to the packet instructions. _(~20 min)_
2. **Cool the rice**: Once cooked, drain the rice in a sieve and spread it out on a tray to help it cool down quickly. _(~10 min)_
3. **Prepare the herbs**: Meanwhile, pick all the herb leaves off the stalks. _(~5 min)_
4. **Prepare the peppers and chilli**: Finely chop the peppers. Halve, deseed and finely chop your chilli. _(~5 min)_
5. **Make the dressing**: Make your lemon dressing. _(~5 min)_
6. **Combine ingredients**: Put your cooled rice into a big serving bowl. Finely chop your herb leaves and add them to the bowl, together with the peppers and chilli. Zest over your lemon, add the dressing and mix well. _(~5 min)_
7. **Season and serve**: Taste, add salt and pepper if you think it needs it, and serve. _(~2 min)_

**Tags**: salad, rice, vegetarian | **Categories**: side dish

---

#### gpt-4o

**Provider**: OpenAI | **Latency**: 11.09s | **Cost**: $0.0089

**Title**: Rice Salad

**Description**: A refreshing rice salad with a mix of herbs and roasted red peppers, best served at room temperature.

**Servings**: 4 | **Difficulty**: easy | **Prep**: 15 min | **Cook**: 15 min | **Total**: 30 min

**Ingredients:**


*To taste*
- sea salt (to taste)
- freshly ground black pepper (to taste)
- 200.0 g roasted red peppers (from a jar)
- 250.0 g mixed long grain and wild rice
- 1.0 fresh red chilli
- fresh basil (a few sprigs)
- 1.0 lemon
- fresh mint (a few sprigs)
- fresh flat-leaf parsley (a few sprigs)
- 4.0 tablespoons lemon dressing (see page 107)

**Instructions:**

1. **Cook the rice**: Bring a large pan of salted water to the boil. Add the rice and cook it according to the packet instructions. Once cooked, drain the rice in a sieve and spread it out on a tray to help it cool down quickly. _(~15 min)_
2. **Prepare the herbs and vegetables**: Pick all the herb leaves off the stalks. Finely chop the roasted red peppers. Halve, deseed, and finely chop the chilli. _(~10 min)_
3. **Mix the salad**: Put the cooled rice into a big serving bowl. Finely chop the herb leaves and add them to the bowl, together with the peppers and chilli. Zest over the lemon, add the lemon dressing, and mix well. _(~5 min)_
4. **Season and serve**: Taste, add salt and pepper if you think it needs it, and serve. _(~5 min)_

**Tags**: salad, rice, vegetarian | **Categories**: Side Dish

---

#### gpt-4o-mini

**Provider**: OpenAI | **Latency**: 18.64s | **Cost**: $0.0006

**Title**: Rice Salad

**Description**: A refreshing rice salad that can be customized with different rice grains and herbs, best served at room temperature.

**Servings**: 4 | **Difficulty**: easy | **Prep**: 15 min | **Cook**: 30 min | **Total**: 45 min

**Ingredients:**


*null*
- 1.0 teaspoon sea salt (to taste)
- 1.0 teaspoon freshly ground black pepper (to taste)
- 200.0 grams roasted red peppers (from a jar)
- 250.0 grams mixed long grain and wild rice (dry)
- 1.0 piece fresh red chilli (halved and deseeded)
- 1.0 bunch fresh basil (few sprigs)
- 1.0 bunch fresh mint (few sprigs)
- 1.0 bunch fresh flat-leaf parsley (few sprigs)
- 1.0 piece lemon (zested and juiced)
- 4.0 tablespoons lemon dressing (see page 107 for recipe)

**Instructions:**


*null*
1. **Boil Water**: Bring a large pan of salted water to the boil. _(~5 min)_
2. **Cook Rice**: Add the rice and cook it according to the packet instructions. _(~20 min)_
3. **Cool Rice**: Once cooked, drain the rice in a sieve and spread it out on a tray to help it cool down quickly. _(~5 min)_
4. **Prepare Herbs**: Meanwhile, pick all the herb leaves off the stalks and finely chop them. _(~5 min)_
5. **Chop Peppers and Chilli**: Finely chop the roasted red peppers. Halve, deseed, and finely chop your fresh red chilli. _(~5 min)_
6. **Make Dressing**: Prepare your lemon dressing as per the recipe. _(~5 min)_
7. **Combine Ingredients**: Put your cooled rice into a big serving bowl. Add the chopped herbs, peppers, and chilli. _(~5 min)_
8. **Finish Salad**: Zest over your lemon, add the dressing, and mix well. Taste and add salt and pepper if needed. _(~5 min)_
9. **Serve**: Serve the salad at room temperature.

**Tags**: salad, rice, vegetarian | **Categories**: side dish, salad

---

#### gemini-2.5-flash

**Provider**: Google | **Latency**: 64.77s | **Cost**: $0.0000

**Error**: Invalid control character at: line 103 column 20 (char 2523)

---

#### claude-3-5-haiku-latest

**Provider**: Anthropic | **Latency**: 12.83s | **Cost**: $0.0000

**Error**: Expecting value: line 1 column 1 (char 0)

---

### IMG_5363.HEIC

#### gemini-2.0-flash-lite

**Provider**: Google | **Latency**: 6.83s | **Cost**: $0.0004

**Title**: Chilli

**Description**: A delicious chilli recipe.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 20 min | **Cook**: 75 min | **Total**: 95 min

**Ingredients:**

- 400.0 g chickpeas (tin)
- 400.0 g red kidney beans (tin)
- 2.0 medium onions
- 2.0 cloves garlic
- 2.0 x 400g tins chopped tomatoes
- 2.0 medium carrots
- 500.0 g minced beef (good-quality)
- 2.0 sticks celery
- 1.0 small bunch fresh coriander
- 2.0 tablespoons balsamic vinegar
- 2.0 red peppers
- 1.0 heaped teaspoon chilli powder
- 1.0 heaped teaspoon ground cumin
- 1.0 heaped teaspoon ground cinnamon
- 400.0 g basmati rice
- 1.0 lime

*To taste*
- to taste sea salt
- to taste black pepper
- 230.0 g natural yogurt (tub)
- 2.0 lugs olive oil

**Instructions:**

1. **Prepare vegetables**: Peel and finely chop the onions, garlic, carrots and celery. Halve the red peppers, remove the stalks and seeds and roughly chop. _(~10 min)_
2. **Sauté vegetables**: Place your largest casserole-type pan on a medium high heat. Add 2 lugs of olive oil and all your chopped vegetables. Add the chilli powder, cumin and cinnamon with a good pinch of salt and pepper. Stir every 30 seconds for around 7 minutes until softened and lightly coloured. _(~10 min)_
3. **Add remaining ingredients**: Add the drained chickpeas, drained kidney beans and the tinned tomatoes. Add the minced beef, breaking any larger chunks up with a wooden spoon. Fill one of the empty tomato tins with water and pour this into the pan. Pick the coriander leaves and place them in the fridge. Finely chop the washed stalks and stir in. Add the balsamic vinegar and season with a good pinch of salt and pepper. _(~10 min)_
4. **Simmer the chilli**: Bring to the boil and turn the heat down to a simmer with a lid slightly askew for about an hour, stirring every now and again to stop it catching. _(~60 min)_
5. **Serve the chilli**: Divide the rice and chilli into big bowls. Sprinkle the chilli with the coriander leaves. _(~5 min)_

**Tags**: chilli, beef, kidney beans | **Categories**: main course

---

#### gemini-2.0-flash

**Provider**: Google | **Latency**: 7.57s | **Cost**: $0.0007

**Title**: Chilli Con Carne

**Description**: A hearty chilli con carne recipe with beef, beans, and spices, served with rice and coriander.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 20 min | **Cook**: 70 min | **Total**: 90 min

**Ingredients:**

- 2.0 medium onions (finely chopped)
- 2.0 cloves garlic (finely chopped)
- 2.0 medium carrots (finely chopped)
- 2.0 sticks celery (finely chopped)
- 2.0 red peppers (roughly chopped)
- 2.0 tablespoons balsamic vinegar
- 1.0 heaped teaspoon chilli powder
- 1.0 heaped teaspoon ground cumin
- 1.0 heaped teaspoon ground cinnamon
- 400.0 g chickpeas (drained)
- 400.0 g red kidney beans (drained)
- 800.0 g chopped tomatoes
- 500.0 g minced beef (good-quality)
- 1.0 small bunch fresh coriander (leaves for garnish, stalks chopped)

*To serve*
- 400.0 g basmati rice
- 230.0 g natural yoghurt
- 1.0 lime

*To taste*
- sea salt (to taste)
- black pepper (to taste)

**Instructions:**

1. **Prepare Vegetables**: Peel and finely chop the onions, garlic, and carrots. Chop the celery. Halve the red peppers, remove the stalks and seeds and roughly chop. _(~15 min)_
2. **Sauté Vegetables and Spices**: Place your largest casserole-type pan on a medium-high heat. Add 2 lugs of olive oil and all your chopped vegetables. Add the chilli powder, cumin and cinnamon with a good pinch of salt and pepper. Stir every 30 seconds for around 7 minutes until softened and lightly coloured. _(~7 min)_
3. **Add Remaining Ingredients and Simmer**: Add the drained chickpeas, drained kidney beans and the tinned tomatoes. Add the minced beef, breaking any larger chunks up with a wooden spoon. Fill one of the empty tomato tins with water and pour this into the pan. Finely chop the washed coriander stalks and stir in. Add the balsamic vinegar and season with a good pinch of salt and pepper. Bring to the boil and turn the heat down to a simmer with a lid slightly askew for about an hour, stirring every now and again to stop it catching. _(~60 min)_

*To serve*
4. **Serve**: Serve with rice. Sprinkle the chilli with the coriander leaves. Serve with a nice hunk of bread, jacket potato or with couscous. Put a small bowl of natural yoghurt on the table; and sprinkle the chilli with the coriander leaves. _(~5 min)_

**Tags**: chilli, beef, beans, spicy, comfort food | **Categories**: Main Course, Dinner

---

#### gemini-2.5-flash-lite

**Provider**: Google | **Latency**: 8.26s | **Cost**: $0.0006

**Title**: Chilli Con Carne

**Description**: A hearty and flavorful chilli con carne, perfect for serving with rice, jacket potatoes, or couscous.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 20 min | **Cook**: 75 min | **Total**: 95 min

**Ingredients:**


*For the Chilli*
- 400.0 g tin chickpeas (drained)
- 400.0 g tin red kidney beans (drained)
- 2.0 x 400g tins chopped tomatoes
- 500.0 g minced beef
- 2.0 medium onions (peeled and finely chopped)
- 2.0 cloves garlic cloves (peeled and finely chopped)
- 2.0 medium carrots (peeled and finely chopped)
- 2.0 sticks celery sticks (finely chopped)
- 2.0 medium red peppers (halved, stalks and seeds removed, roughly chopped)
- 2.0 tablespoons balsamic vinegar
- 1.0 heaped teaspoon chilli powder
- 1.0 heaped teaspoon ground cumin
- 1.0 heaped teaspoon ground cinnamon

*To Serve*
- 400.0 g basmati rice
- 1.0 230g tub of g (This ingredient is unclear from the OCR. Assuming it's sour cream or similar.)

*For the Chilli*
- 1.0 small bunch fresh coriander (leaves picked for garnish, stalks finely chopped)
- 2.0 lugs olive oil (for frying)

*To taste*
- 1.0 good pinch sea salt (to taste)
- 1.0 good pinch freshly ground black pepper (to taste)

**Instructions:**


*For the Chilli*
1. **Prepare Vegetables**: Peel and finely chop the onions, garlic, carrots, and celery. Halve the red peppers, remove the stalks and seeds, and roughly chop. _(~10 min)_
2. **Sauté Vegetables**: Place your largest casserole-type pan on a medium-high heat. Add 2 lugs of olive oil and all your chopped vegetables. Add the chilli powder, cumin, and cinnamon with a good pinch of salt and pepper. Stir every 30 seconds for around 7 minutes until softened and lightly coloured. _(~7 min)_
3. **Add Remaining Chilli Ingredients**: Add the drained chickpeas, drained kidney beans, and the tinned tomatoes. Add the minced beef, breaking any larger chunks up with a wooden spoon. Fill one of the empty tomato tins with water and pour this into the pan. Pick the coriander leaves and place them in the fridge. Finely chop the washed stalks and stir in. Add the balsamic vinegar and season with a good pinch of salt and pepper. _(~5 min)_
4. **Simmer the Chilli**: Bring to the boil and turn the heat down to a simmer with a lid slightly askew for about an hour, stirring every now and again to stop it catching. _(~60 min)_

*To Serve*
5. **Cook Rice**: Cook the basmati rice according to package directions (or refer to pages 95-96 as indicated in the original text). _(~15 min)_
6. **Serve**: Divide the rice and chilli into big bowls. Sprinkle the chilli with the reserved coriander leaves. Serve with a nice hunk of crusty bread, a jacket potato, couscous, or a green salad. _(~5 min)_

**Tags**: chilli, con carne, beef, beans, tomatoes, spicy | **Categories**: Main Course, Chilli

---

#### gpt-4o

**Provider**: OpenAI | **Latency**: 15.45s | **Cost**: $0.0135

**Title**: Chilli Con Carne

**Description**: A hearty and flavorful chilli con carne, perfect for serving with rice or potatoes.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 72 min | **Total**: 87 min

**Ingredients:**


*For the chilli*
- 400.0 g chickpeas (tin)
- 400.0 g red kidney beans (tin)
- 800.0 g chopped tomatoes (tins)
- 500.0 g minced beef (good-quality)
- 2.0 medium onions (peeled and finely chopped)
- 2.0 cloves garlic cloves (peeled and finely chopped)
- 2.0 medium carrots (peeled and finely chopped)
- 2.0 sticks celery sticks (chopped)

*For the garnish*
- 1.0 small bunch fresh coriander (leaves picked, stalks finely chopped)

*For the chilli*
- 2.0 tablespoons balsamic vinegar
- 2.0 pieces red peppers (halved, stalks and seeds removed, roughly chopped)
- 1.0 heaped teaspoon chilli powder
- 1.0 heaped teaspoon ground cumin
- 1.0 heaped teaspoon ground cinnamon

*For serving*
- 400.0 g basmati rice
- 1.0 piece lime

*To taste*
- sea salt (to taste)
- freshly ground black pepper (to taste)

**Instructions:**


*For the chilli*
1. **Prepare vegetables**: Peel and finely chop the onions, garlic, carrots, and celery. Halve the red peppers, remove the stalks and seeds, and roughly chop. _(~10 min)_
2. **Cook vegetables**: Place your largest casserole-type pan on medium-high heat. Add 2 lugs of olive oil and all your chopped vegetables. Add the chilli powder, cumin, and cinnamon with a good pinch of salt and pepper. Stir every 30 seconds for around 7 minutes until softened and lightly coloured. _(~7 min)_
3. **Add main ingredients**: Add the drained chickpeas, drained kidney beans, and the tinned tomatoes. Add the minced beef, breaking any larger chunks up with a wooden spoon. Fill one of the empty tomato tins with water and pour this into the pan. _(~5 min)_
4. **Simmer chilli**: Pick the coriander leaves and place them in the fridge. Finely chop the washed stalks and stir in. Add the balsamic vinegar and season with a good pinch of salt and pepper. Bring to the boil and turn the heat down to a simmer with a lid slightly askew for about an hour, stirring every now and again to stop it catching. _(~60 min)_

*For serving*
5. **Serve**: Serve the chilli with basmati rice, lime wedges, and a sprinkle of coriander leaves. Optionally, serve with a green salad or natural yogurt. _(~5 min)_

**Tags**: spicy, comfort food, main course | **Categories**: Main Dish

---

#### gpt-4o-mini

**Provider**: OpenAI | **Latency**: 26.69s | **Cost**: $0.0008

**Title**: Chilli Con Carne

**Description**: A hearty and flavorful chilli con carne made with minced beef, beans, and spices, perfect for serving with rice or bread.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 60 min | **Total**: 75 min

**Ingredients:**


*For the chilli*
- 400.0 grams chickpeas (drained)
- 400.0 grams red kidney beans (drained)
- 800.0 grams chopped tomatoes (2 tins)
- 500.0 grams minced beef (good-quality)
- 2.0 medium onions (finely chopped)
- 2.0 cloves garlic (finely chopped)
- 2.0 medium carrots (finely chopped)
- 2.0 sticks celery (finely chopped)
- 2.0 small red peppers (roughly chopped)
- 2.0 tablespoons balsamic vinegar
- 1.0 heaped teaspoon chilli powder
- 1.0 heaped teaspoon ground cumin
- 1.0 heaped teaspoon ground cinnamon

*To taste*
- sea salt (to taste)
- black pepper (to taste)

*For the garnish*
- 1.0 small bunch fresh coriander (leaves for garnish)

*For serving*
- 400.0 grams basmati rice (for serving)

**Instructions:**


*For the chilli*
1. **Prepare the vegetables**: Peel and finely chop the onions, garlic, and carrots. Halve the red peppers, remove the stalks and seeds, and roughly chop. _(~10 min)_
2. **Cook the vegetables**: Place your largest casserole-type pan on medium-high heat. Add 2 lugs of olive oil and all your chopped vegetables. Stir every 30 seconds for around 7 minutes until softened and lightly coloured. _(~7 min)_
3. **Add spices and beans**: Add the chilli powder, cumin, and cinnamon with a good pinch of salt and pepper. Stir well. Then add the drained chickpeas, drained kidney beans, and the tinned tomatoes. _(~5 min)_
4. **Add the beef**: Add the minced beef, breaking any larger chunks up with a wooden spoon. Fill one of the empty tomato tins with water and pour this into the pan. _(~5 min)_
5. **Simmer the chilli**: Pick the coriander leaves and place them in the fridge. Finely chop the washed stalks and stir in. Add the balsamic vinegar and season with a good pinch of salt and pepper. Bring to the boil and turn the heat down to a simmer with a lid slightly askew for about an hour, stirring occasionally to prevent sticking. _(~60 min)_

*For serving*
6. **Serve the chilli**: Serve the chilli in big bowls with basmati rice or with jacket potatoes or couscous. Garnish with coriander leaves. _(~5 min)_

**Tags**: chilli, beef, comfort food | **Categories**: main dish

---

#### gemini-2.5-flash

**Provider**: Google | **Latency**: 28.68s | **Cost**: $0.0000

**Error**: 500 An internal error has occurred. Please retry or report in https://developers.generativeai.google/guide/troubleshooting

---

#### claude-3-5-haiku-latest

**Provider**: Anthropic | **Latency**: 16.20s | **Cost**: $0.0000

**Error**: Expecting value: line 1 column 1 (char 0)

---

### IMG_5365.HEIC

#### gemini-2.5-flash-lite

**Provider**: Google | **Latency**: 2.84s | **Cost**: $0.0005

**Title**: Cauliflower Cheese

**Description**: A classic cauliflower cheese dish with a creamy sauce and a crispy breadcrumb topping.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 20 min | **Cook**: 55 min | **Total**: 75 min

**Ingredients:**


*For the Cauliflower*
- 1.0 large cauliflower (Remove outer green leaves, break into small pieces, slice up the stalk)
- pinch sea salt

*For the Sauce*
- 4.0 anchovy fillets (Chop up)
- 400.0 ml creme fraiche
- 100.0 g grated Cheddar cheese
- salt
- pepper

*For the Breadcrumbs*
- lug extra virgin olive oil
- 4.0 slices bread (Crusts left on)
- 1.0 rasher smoked streaky bacon (preferably free-range or organic)
- 2.0 sprigs fresh rosemary (Pick leaves off)

*For the Topping*
- 100.0 g grated Cheddar cheese

**Instructions:**


*Preparation*
1. **Preheat Oven and Prepare Cauliflower**: Preheat your oven to 180°C/350°F/gas 4. Put your kettle on. Remove the outer green leaves from a large cauliflower and discard. Break the cauliflower into small pieces and slice up the stalk. Pick the leaves off 2 sprigs of fresh rosemary. _(~5 min)_
2. **Boil Cauliflower**: Add all the cauliflower to the pan of boiling water with a pinch of sea salt and boil for 5 minutes. _(~5 min)_

*Sauce Preparation*
3. **Prepare the Sauce**: Chop up 4 anchovy fillets and put them into a bowl with 400ml of creme fraiche. Stir in 100g of grated Cheddar cheese and season with salt and pepper. _(~5 min)_

*Topping Preparation*
4. **Make the Breadcrumbs**: Pour a lug of extra virgin olive oil into a food processor and add 4 slices of bread with the crusts left on, a rasher of smoked streaky bacon, and the rosemary leaves. Whiz everything up until you have breadcrumbs. _(~5 min)_

*Baking*
5. **Assemble and Bake**: Drain the boiled cauliflower in a colander and place it into a medium-sized baking dish. Spoon the sauce over the cauliflower, and sprinkle over another 100g of grated Cheddar followed by your breadcrumbs. Place in the preheated oven for 45 minutes or until golden, crisp and bubbling. _(~45 min)_

**Tags**: cauliflower, cheese, gratin, comfort food | **Categories**: Main Course, Side Dish

---

#### gemini-2.0-flash

**Provider**: Google | **Latency**: 7.00s | **Cost**: $0.0006

**Title**: Cauliflower Cheese

**Description**: A classic cauliflower cheese recipe with anchovies and a rosemary breadcrumb topping.

**Servings**: 5 | **Difficulty**: easy | **Prep**: 15 min | **Cook**: 55 min | **Total**: 70 min

**Ingredients:**

- 1.0 large cauliflower (outer green leaves removed, broken into small pieces, stalk sliced)
- 2.0 sprigs fresh rosemary (leaves picked)
- 4.0 anchovy fillets (chopped)
- 400.0 ml creme fraiche
- 100.0 g Cheddar cheese (grated)
- 100.0 g Cheddar cheese (grated)
- lug extra virgin olive oil
- 4.0 slices bread (crusts left on)
- 1.0 rasher smoked streaky bacon (preferably free-range or organic)
- pinch sea salt
- to taste salt
- to taste pepper

**Instructions:**

1. **Preheat oven**: Preheat your oven to 180°C/350°F/gas 4. _(~2 min)_
2. **Boil water and prepare cauliflower**: Put your kettle on, then pour the boiling water into a large pan. Remove the outer green leaves from 1 large cauliflower and discard. Break the cauliflower into small pieces and slice up the stalk. Pick the leaves off 2 sprigs of fresh rosemary. Add all the cauliflower to the pan of boiling water with a pinch of sea salt and boil for 5 minutes. _(~10 min)_
3. **Make the sauce**: Chop up 4 anchovy fillets and put them into a bowl with 400ml of creme fraiche. Stir in 100g of grated Cheddar cheese and season with salt and pepper. _(~5 min)_
4. **Make the breadcrumbs**: Pour a lug of extra virgin olive oil into a food processor and add 4 slices of bread with the crusts left on, a rasher of smoked streaky bacon, preferably free-range or organic, and the rosemary leaves. Whiz everything up until you have breadcrumbs. _(~5 min)_
5. **Assemble and bake**: By now your cauliflower should be done, so drain it in a colander and place it into a medium-sized baking dish. Spoon the sauce over the cauliflower, and sprinkle over another 100g of grated Cheddar followed by your breadcrumbs. Place in the preheated oven for 45 minutes or until golden, crisp and bubbling. _(~50 min)_

**Tags**: cauliflower, cheese, anchovy, rosemary, breadcrumbs, bacon | **Categories**: Vegetable dishes, Main course

---

#### gemini-2.0-flash-lite

**Provider**: Google | **Latency**: 8.41s | **Cost**: $0.0005

**Title**: Cauliflower Cheese

**Description**: A classic and comforting dish.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 45 min | **Total**: 60 min

**Ingredients:**

- 1.0 large cauliflower (outer green leaves removed and discarded)
- pinch sea salt
- 4.0 anchovy fillets (chopped)
- 400.0 ml creme fraiche
- 100.0 g grated Cheddar cheese
- to taste salt
- to taste pepper
- lug extra virgin olive oil
- 4.0 bread slices (with crusts)
- 1.0 rasher smoked streaky bacon (free-range or organic, preferably)
- leaves rosemary leaves (from 2 sprigs)
- 100.0 g grated Cheddar cheese

**Instructions:**

1. **Preheat Oven and Prepare Cauliflower**: Preheat oven to 180°C/350°F/gas 4. Put your kettle on, then pour the boiling water into a large pan. Remove the outer green leaves from the cauliflower and discard. Break the cauliflower into small pieces and slice up the stalk. _(~5 min)_
2. **Boil Cauliflower**: Add all the cauliflower to the pan of boiling water with a pinch of sea salt and boil for 5 minutes. _(~5 min)_
3. **Make Sauce**: Chop up the anchovy fillets and put them into a bowl with the creme fraiche. Stir in 100g of grated Cheddar cheese and season with salt and pepper. _(~5 min)_
4. **Make Breadcrumbs**: Pour a lug of extra virgin olive oil into a food processor and add the bread slices with the crusts left on, the rasher of smoked streaky bacon, and the rosemary leaves. Whiz everything up until you have breadcrumbs. _(~5 min)_
5. **Assemble and Bake**: Drain the cauliflower in a colander and place it into a medium-sized baking dish. Spoon the sauce over the cauliflower, and sprinkle over another 100g of grated Cheddar followed by your breadcrumbs. Place in the preheated oven for 45 minutes or until golden, crisp and bubbling. _(~45 min)_

**Tags**: cauliflower, cheese, baking | **Categories**: main course

---

#### claude-3-5-haiku-latest

**Provider**: Anthropic | **Latency**: 15.02s | **Cost**: $0.0059

**Title**: Cauliflower Cheese

**Description**: A classic British vegetable side dish with crispy breadcrumb topping and cheesy sauce

**Servings**: 5 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 45 min | **Total**: 60 min

**Ingredients:**


*For the cauliflower*
- 1 whole cauliflower (outer green leaves removed, broken into small pieces)

*For the topping*
- 2 sprigs fresh rosemary

*To taste*
- 1 pinch sea salt

*For the sauce*
- 4 whole anchovy fillets
- 400 ml creme fraiche
- 200 g Cheddar cheese (grated, divided into 100g portions)

*To taste*
- black pepper

*For the topping*
- 1 lug extra virgin olive oil
- 4 slices bread (with crusts left on)
- 1 rasher smoked streaky bacon (preferably free-range or organic)

**Instructions:**

1. **Preheat Oven**: Preheat your oven to 180°C/350°F/gas 4 _(~5 min)_

*Preparation*
2. **Prepare Cauliflower**: Remove outer green leaves from cauliflower and discard. Break cauliflower into small pieces and slice up the stalk. Pick rosemary leaves off sprigs. _(~5 min)_

*Cooking Cauliflower*
3. **Boil Cauliflower**: Add cauliflower to boiling water with a pinch of sea salt. Boil for 5 minutes. _(~5 min)_

*Sauce Preparation*
4. **Prepare Sauce**: Chop anchovy fillets and mix with creme fraiche. Stir in 100g of grated Cheddar cheese. Season with salt and pepper. _(~3 min)_

*Topping Preparation*
5. **Make Breadcrumbs**: In a food processor, combine olive oil, bread slices, bacon, and rosemary leaves. Blend until you have breadcrumbs. _(~2 min)_

*Assembly*
6. **Assemble Dish**: Drain cauliflower and place in a medium-sized baking dish. Spoon sauce over cauliflower. Sprinkle remaining 100g of Cheddar cheese and breadcrumbs on top. _(~5 min)_

*Baking*
7. **Bake**: Place in preheated oven and bake for 45 minutes or until golden, crisp, and bubbling. _(~45 min)_

**Tags**: vegetarian, side dish, british cuisine | **Categories**: side dish, vegetable

---

#### gpt-4o-mini

**Provider**: OpenAI | **Latency**: 15.98s | **Cost**: $0.0005

**Title**: Cauliflower Cheese

**Description**: A creamy and cheesy baked cauliflower dish topped with breadcrumbs.

**Servings**: 6 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 45 min | **Total**: 60 min

**Ingredients:**

- 1.0 large cauliflower (outer green leaves removed)
- 1.0 pinch sea salt
- 4.0 fillets anchovy fillets (chopped)
- 400.0 ml creme fraiche
- 200.0 g Cheddar cheese (100g for sauce, 100g for topping)
- 1.0 lug extra virgin olive oil
- 4.0 slices bread (crusts left on)
- 1.0 rasher smoked streaky bacon (preferably free-range or organic)
- 2.0 sprigs fresh rosemary (leaves picked)

**Instructions:**

1. **Preheat the oven**: Preheat your oven to 180°C/350°F/gas 4. _(~10 min)_
2. **Boil the cauliflower**: Pour boiling water into a large pan and add the cauliflower pieces with a pinch of sea salt. Boil for 5 minutes. _(~5 min)_
3. **Prepare the sauce**: In a bowl, combine the chopped anchovy fillets, creme fraiche, and 100g of grated Cheddar cheese. Season with salt and pepper. _(~5 min)_
4. **Make breadcrumbs**: In a food processor, add the olive oil, bread slices, smoked bacon, and rosemary leaves. Whiz until you have breadcrumbs. _(~5 min)_
5. **Combine and bake**: Drain the cauliflower and place it in a medium-sized baking dish. Spoon the sauce over the cauliflower, sprinkle with another 100g of grated Cheddar, and top with breadcrumbs. Bake in the preheated oven for 45 minutes or until golden, crisp, and bubbling. _(~45 min)_

**Tags**: vegetarian, baked, cheesy | **Categories**: main dish, vegetable

---

#### gpt-4o

**Provider**: OpenAI | **Latency**: 17.33s | **Cost**: $0.0104

**Title**: Cauliflower Cheese

**Description**: A delicious baked dish featuring cauliflower in a creamy cheese sauce, topped with breadcrumbs.

**Servings**: 5 | **Difficulty**: medium | **Prep**: 25 min | **Cook**: 45 min | **Total**: 70 min

**Ingredients:**


*For the main dish*
- 1.0 large cauliflower (outer green leaves removed)
- 2.0 sprigs fresh rosemary (leaves picked)

*To taste*
- sea salt (to taste)

*For the sauce*
- 4.0 anchovy fillets (chopped)
- 400.0 ml creme fraiche
- 200.0 g Cheddar cheese (grated, divided)

*To taste*
- salt and pepper (to taste)

*For the topping*
- lug extra virgin olive oil
- 4.0 slices bread slices (crusts left on)
- 1.0 rasher smoked streaky bacon (preferably free-range or organic)

**Instructions:**


*For the main dish*
1. **Preheat Oven**: Preheat your oven to 180°C/350°F/gas 4. _(~5 min)_
2. **Boil Cauliflower**: Put your kettle on, then pour the boiling water into a large pan. Add all the cauliflower to the pan with a pinch of sea salt and boil for 5 minutes. _(~10 min)_

*For the sauce*
3. **Prepare Sauce**: Chop up 4 anchovy fillets and put them into a bowl with 400ml of creme fraiche. Stir in 100g of grated Cheddar cheese and season with salt and pepper. _(~5 min)_

*For the topping*
4. **Make Breadcrumbs**: Pour a lug of extra virgin olive oil into a food processor and add 4 slices of bread, a rasher of smoked streaky bacon, and the rosemary leaves. Whiz everything up until you have breadcrumbs. _(~5 min)_

*For the main dish*
5. **Assemble Dish**: Drain the cauliflower in a colander and place it into a medium-sized baking dish. Spoon the sauce over the cauliflower, and sprinkle over another 100g of grated Cheddar followed by your breadcrumbs. _(~5 min)_
6. **Bake**: Place in the preheated oven for 45 minutes or until golden, crisp, and bubbling. _(~45 min)_

**Tags**: vegetarian, baked, comfort food | **Categories**: Side Dish

---

#### gemini-2.5-flash

**Provider**: Google | **Latency**: 34.96s | **Cost**: $0.0010

**Title**: Cauliflower Cheese

**Description**: A comforting and savory cauliflower cheese bake, featuring a creamy anchovy-cheddar sauce, topped with crispy bacon-rosemary breadcrumbs.

**Servings**: 4 | **Difficulty**: easy | **Prep**: 20 min | **Cook**: 50 min | **Total**: 70 min

**Ingredients:**


*For the Cauliflower*
- 1.0 large cauliflower
- 1.0 pinch sea salt

*For the Sauce*
- 4.0 anchovy fillets (chopped)
- 400.0 ml creme fraiche
- 100.0 g grated Cheddar cheese
- salt (to taste)
- pepper (to taste)

*For the Topping*
- 1.0 tablespoon extra virgin olive oil (a lug)
- 4.0 slices of bread (with crusts left on)
- 1.0 rasher smoked streaky bacon (preferably free-range or organic)
- 2.0 sprigs fresh rosemary (leaves picked)
- 100.0 g grated Cheddar cheese (for sprinkling)

**Instructions:**


*Preparation*
1. **Preheat Oven and Prepare Water**: Preheat your oven to 180°C/350°F/gas 4. Put your kettle on, then pour the boiling water into a large pan. _(~10 min)_
2. **Prepare Cauliflower**: Remove the outer green leaves from 1 large cauliflower and discard. Break the cauliflower into small pieces and slice up the stalk. Add all the cauliflower to the pan of boiling water with a pinch of sea salt and boil for 5 minutes. _(~10 min)_

*Making the Sauce*
3. **Prepare the Sauce**: While the cauliflower boils, chop up 4 anchovy fillets and put them into a bowl with 400ml of creme fraiche. Stir in 100g of grated Cheddar cheese and season with salt and pepper. _(~5 min)_

*Making the Topping*
4. **Prepare the Topping**: Pick the leaves off 2 sprigs of fresh rosemary. Pour approximately 1 tablespoon (a 'lug') of extra virgin olive oil into a food processor and add 4 slices of bread with the crusts left on, 1 rasher of smoked streaky bacon, and the rosemary leaves. Whiz everything up until you have breadcrumbs. _(~5 min)_

*Assembly & Baking*
5. **Assemble the Dish**: By now your cauliflower should be done, so drain it in a colander and place it into a medium-sized baking dish. Spoon the sauce evenly over the cauliflower, and sprinkle over another 100g of grated Cheddar, followed by your prepared breadcrumbs. _(~5 min)_
6. **Bake**: Place the baking dish in the preheated oven for 45 minutes or until golden, crisp, and bubbling. _(~45 min)_

**Tags**: Cauliflower, Cheese, Bake, Vegetable, Side Dish, Comfort Food | **Categories**: Main Dish, Side Dish

---

### IMG_5482.HEIC

#### gemini-2.5-flash-lite

**Provider**: Google | **Latency**: 4.07s | **Cost**: $0.0007

**Title**: Raspberry Cheesecake

**Description**: A wonderfully light and crisp cheesecake with a raspberry topping, balanced with almonds for extra texture and nuttiness.

**Servings**: 8 | **Difficulty**: medium | **Prep**: 30 min | **Cook**: 180 min | **Total**: 210 min

**Ingredients:**


*For the base*
- 200.0 g digestive biscuits (or other plain biscuits)
- 50.0 g almonds (blitzed)
- 100.0 g butter (melted)

*For the filling*
- 500.0 g cream cheese (full-fat)
- 250.0 g ricotta (full-fat)
- 150.0 g sugar
- 0.5 tsp salt
- 2.0 tbsp cornflour
- 1.0 tbsp lemon zest
- 2.0 tbsp lemon juice
- 2.0 eggs

*For the raspberry topping*
- 300.0 g raspberries (fresh or frozen)
- 2.0 tbsp sugar
- 1.0 tbsp lemon juice
- 0.5 tsp rose essence (optional)

*For the garnish*
- rose petals (for decoration, optional)

**Instructions:**


*For the base*
1. **Preheat Oven and Prepare Tin**: Preheat the oven to 160°C (300°F/gas 2). Grease and line a 23 cm (9 in) loose-bottomed cake tin with baking paper. _(~5 min)_
2. **Make the Base**: Blitz the digestive biscuits and almonds together in a food processor until you have a fine crumb. Add the melted butter and blitz again until combined. Alternatively, rub the butter into the biscuit and almond mixture by hand until it resembles breadcrumbs. Press this mixture evenly over the base of the lined tin using the back of a spoon. _(~10 min)_
3. **Bake the Base**: Bake for 30 minutes until golden. Remove from the oven and set aside to cool. _(~30 min)_

*For the filling*
4. **Make the Filling**: In a food processor or bowl, blend the cream cheese, ricotta, sugar, and salt until smooth. Mix the cornflour with the lemon zest and juice and stir well to dissolve. Beat this mixture into the cream cheese mix. Add the eggs one at a time, beating well after each addition until the filling is smooth. _(~15 min)_
5. **Pour Filling onto Base**: Pour the filling over the baked and cooled base. It will look very loose, but this is normal. _(~2 min)_
6. **Bake the Cheesecake**: Bake in the oven for 50 minutes. Turn off the oven, leave the door slightly ajar, and allow the cheesecake to cook gently in the residual heat for another 50 minutes. _(~100 min)_
7. **Cool the Cheesecake**: Remove the cheesecake from the oven and allow it to cool completely. Chill in the refrigerator for at least 1 hour before serving. _(~60 min)_

*For the raspberry topping*
8. **Make the Raspberry Topping**: Cook the raspberries with the sugar and lemon juice over a medium heat for about 8-10 minutes until you have a loose jam consistency. Remove from the heat. Ladle off a spoonful of the juice and mix it with the cornflour in a small bowl until dissolved. Add this mixture back to the pan with the raspberries and stir over the heat for a minute or two until the mixture thickens. Remove from the heat and let it cool. _(~15 min)_

*For the garnish*
9. **Assemble and Serve**: Stir the optional rose essence into the cooled raspberry mixture. Top the cooled cheesecake with the raspberry mixture. Decorate with optional rose petals if desired. Serve. _(~5 min)_

**Tags**: cheesecake, raspberry, dessert, baked | **Categories**: Desserts, Cakes

---

#### gemini-2.0-flash-lite

**Provider**: Google | **Latency**: 11.32s | **Cost**: $0.0006

**Title**: Ricotta Cheesecake with Raspberry Compote

**Description**: A light and airy cheesecake with a biscuit base, topped with a fresh raspberry compote.

**Servings**: 8 | **Difficulty**: medium | **Prep**: 30 min | **Cook**: 100 min | **Total**: 190 min

**Ingredients:**

- butter (for the base)
- almonds (for the base)
- cream cheese (for the filling)
- ricotta (for the filling)
- sugar (for the filling)
- salt (for the filling)
- cornflour (for the filling)
- lemon zest (for the filling)
- lemon juice (for the filling)
- eggs (for the filling)

*For the raspberry compote*
- raspberries (for the raspberry compote)
- lemon juice (for the raspberry compote)
- sugar (for the raspberry compote)
- rose essence (optional)
- rose petals (optional)

**Instructions:**

1. **Prepare the oven and tin**: Preheat the oven to 160°C (300°F/gas 2). Grease and line a 23 cm (9 in) loose-bottomed cake tin (pan) with baking paper. _(~5 min)_
2. **Make the base**: Blitz the ingredients for the base together in a food processor until you have a fine crumb (or rub the butter in by hand as if making a crumble - the almonds will break up sufficiently between firm fingers). Using the back of a spoon, press this mixture over the base of the lined tin to form an even layer. _(~10 min)_
3. **Bake the base**: Bake for 30 minutes until golden. Remove and set aside to cool. _(~30 min)_
4. **Make the filling**: Blend the cream cheese, ricotta, sugar and salt, and blitz/whisk until smooth. Mix the cornflour with the lemon zest and juice and stir well to dissolve. Beat this into the cream mix, then beat in the eggs, one at a time, until smooth. Pour the filling over the baked base. It will look very loose, but don’t worry, all is well. _(~15 min)_
5. **Bake the cheesecake**: Bake in the oven for 50 minutes, then turn off the oven, leave the door open and leave the cheesecake to cook gently in the residual heat for another 50 minutes. _(~100 min)_

*For the raspberry compote*
6. **Make the raspberry compote**: For the raspberry compote, cook the raspberries over a low heat with the lemon juice and sugar for about 8-10 minutes until you have a loose jam. Remove from the heat, ladle off a spoonful of juice and add it to the cornflour. Stir well until the flour dissolves, then add it to the pan and stir over the heat for a minute or two (the cornflour makes the raspberry mixture thicken without you having to reduce it down and cook out all the fresh flavour of the raspberries). Remove from the heat, decant into a bowl and leave to cool. _(~20 min)_
7. **Assemble and serve**: Stir the rose essence into the raspberry mixture (if you like - it's also very good kept simply raspberry), then top your cooled cheesecake with it. Serve, with added rose petals if you wish. Chill for at least 1 hour before serving. _(~10 min)_

**Tags**: cheesecake, raspberry, dessert | **Categories**: desserts

---

#### gemini-2.0-flash

**Provider**: Google | **Latency**: 11.52s | **Cost**: $0.0008

**Title**: Ricotta Cheesecake with Raspberry Topping

**Description**: A light and airy cheesecake made with ricotta cheese, topped with a fresh raspberry compote.

**Servings**: 8 | **Difficulty**: medium | **Prep**: 25 min | **Cook**: 180 min | **Total**: 205 min

**Ingredients:**


*For the base*
- almonds (for extra texture and nuttiness)
- butter

*For the filling*
- cream cheese
- ricotta
- sugar
- salt
- cornflour
- lemon zest
- lemon juice
- eggs

*For the raspberry topping*
- raspberries
- lemon juice
- sugar
- cornflour
- rose essence (optional)
- rose petals (for serving, optional)

**Instructions:**

1. **Preheat oven and prepare tin**: Preheat the oven to 160°C (300°F/gas 2). Grease and line a 23 cm (9 in) loose-bottomed cake tin (pan) with baking paper. _(~5 min)_
2. **Make the base**: Blitz the ingredients for the base together in a food processor until you have a fine crumb (or rub the butter in by hand as if making a crumble - the almonds will break up sufficiently between firm fingers). Using the back of a spoon, press this mixture over the base of the lined tin to form an even layer. _(~10 min)_
3. **Bake the base**: Bake for 30 minutes until golden. Remove and set aside to cool. _(~30 min)_
4. **Make the filling**: Meanwhile, make the filling. Blend the cream cheese, ricotta, sugar and salt, and blitz/whisk until smooth. Mix the cornflour with the lemon zest and juice and stir well to dissolve. Beat this into the cream mix, then beat in the eggs, one at a time, until smooth. Pour the filling over the baked base. It will look very loose, but don’t worry, all is well. _(~15 min)_
5. **Bake the cheesecake**: Bake in the oven for 50 minutes, then turn off the oven, leave the door open and leave the cheesecake to cook gently in the residual heat for another 50 minutes. _(~100 min)_
6. **Cool the cheesecake**: Remove and allow to cool. _(~60 min)_
7. **Make the raspberry topping**: For the raspberry layer, cook the raspberries over a low heat with the lemon juice and sugar for about 8-10 minutes until you have a loose jam. Remove from the heat, ladle off a spoonful of juice and add it to the cornflour. Stir well until the flour dissolves, then add it to the pan and stir over the heat for a minute or two (the cornflour makes the raspberry mixture thicken without you having to reduce it down and cook out all the fresh flavour of the raspberries). Remove from the heat, decant into a bowl and leave to cool. _(~15 min)_
8. **Assemble and chill**: Stir the rose essence into the raspberry mixture (if you like - it's also very good kept simply raspberry), then top your cooled cheesecake with it. Serve, with added rose petals if you wish. Chill for at least 1 hour before serving. _(~60 min)_

**Tags**: cheesecake, raspberry, ricotta, dessert | **Categories**: desserts

---

#### gemini-2.5-flash

**Provider**: Google | **Latency**: 21.51s | **Cost**: $0.0014

**Title**: Cheesecake with Raspberry Cream

**Description**: Using mostly ricotta means that this cheesecake is wonderfully light rather than overpowering, in that magical way ricotta has of making everything it touches feel baked into a beguiling and contradistinctive texture: rich and light. Creating your own biscuit base is easy. I add some almonds for extra texture and nuttiness, but wonderfully crisp; Goldilocks-balanced. The topping is fresh and sharp, a quick jam/compôte lifted by a little rosy perfume. Note: Ingredient quantities are missing from the provided text.

**Servings**: 8 | **Difficulty**: medium | **Prep**: 45 min | **Cook**: 140 min | **Total**: 185 min

**Ingredients:**


*For the Base*
- Ingredients for the base (Quantities not specified in text. Implied ingredients include butter, biscuits/cookies, and almonds.)

*For the Filling*
- Cream cheese (Quantities not specified in text.)
- Ricotta (Quantities not specified in text.)
- Sugar (Quantities not specified in text.)
- Salt (Quantities not specified in text.)
- Cornflour (Quantities not specified in text.)
- Lemon zest (Quantities not specified in text.)
- Lemon juice (Quantities not specified in text.)
- Eggs (Quantities not specified in text.)

*For the Raspberry Topping*
- Raspberries (Quantities not specified in text.)
- Lemon juice (Quantities not specified in text.)
- Sugar (Quantities not specified in text.)
- Cornflour (Quantities not specified in text.)
- Rose essence (Optional, quantities not specified in text.)

*For Serving*
- Rose petals (Optional, for serving. Quantities not specified in text.)

**Instructions:**


*For the Base*
1. **Prepare Baking Tin**: Preheat the oven to 160°C (300°F/gas 2). Grease and line a 23 cm (9 in) loose-bottomed cake tin (pan) with baking paper. _(~5 min)_
2. **Make the Base Mixture**: Blitz the ingredients for the base together in a food processor until you have a fine crumb (or rub the butter in by hand as if making a crumble - the almonds will break up sufficiently between firm fingers). _(~10 min)_
3. **Form and Bake the Base**: Using the back of a spoon, press this mixture over the base of the lined tin to form an even layer. Bake for 30 minutes until golden. Remove and set aside to cool. _(~45 min)_

*For the Filling*
4. **Prepare the Filling Mixture**: Meanwhile, make the filling. Blend the cream cheese, ricotta, sugar and salt, and blitz/whisk until smooth. _(~5 min)_
5. **Add Cornflour, Lemon, and Eggs**: Mix the cornflour with the lemon zest and juice and stir well to dissolve. Beat this into the cream mix, then beat in the eggs, one at a time, until smooth. _(~10 min)_
6. **Pour Filling Over Base**: Pour the filling over the baked base. It will look very loose, but don’t worry, all is well. _(~2 min)_
7. **Bake the Cheesecake**: Bake in the oven for 50 minutes, then turn off the oven, leave the door open and leave the cheesecake to cook gently in the residual heat for another 50 minutes. _(~100 min)_
8. **Cool the Cheesecake**: Remove and allow to cool for at least 1 hour before serving. _(~60 min)_

*For the Raspberry Topping*
9. **Make Raspberry Jam/Compôte**: For the raspberry layer, cook the raspberries over a low heat with the lemon juice and sugar for about 8-10 minutes until you have a loose jam. _(~10 min)_
10. **Thicken Raspberry Topping**: Remove from the heat, ladle off a spoonful of juice and add it to the cornflour. Stir well until the flour dissolves, then add it to the pan and stir over the heat for a minute or two (the cornflour makes the raspberry mixture thicken without you having to reduce it down and cook out all the fresh flavour of the raspberries). _(~5 min)_
11. **Cool Raspberry Topping**: Remove from the heat, decant into a bowl and leave to cool. _(~15 min)_
12. **Finish and Top Cheesecake**: Stir the rose essence into the raspberry mixture (if you like - it's also very good kept simply raspberry), then top your cooled cheesecake with it. _(~5 min)_

*For Serving*
13. **Serve**: Serve, with added rose petals if you wish.

**Tags**: cheesecake, raspberry, dessert, baked | **Categories**: Dessert

---

#### gpt-4o-mini

**Provider**: OpenAI | **Latency**: 22.70s | **Cost**: $0.0009

**Title**: Ricotta Cheesecake with Raspberry Topping

**Description**: A wonderfully light cheesecake made with ricotta, topped with a fresh raspberry sauce.

**Servings**: 8 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 140 min | **Total**: 155 min

**Ingredients:**


*For the filling*
- 500.0 grams ricotta cheese (for the filling)
- 250.0 grams cream cheese (for the filling)
- 150.0 grams sugar (for the filling)
- 1.0 teaspoon salt (for the filling)
- 2.0 tablespoons cornflour (for thickening)
- 1.0 tablespoon lemon zest (for the filling)
- 2.0 tablespoons lemon juice (for the filling)
- 3.0 large eggs (for the filling)

*For the base*
- 200.0 grams digestive biscuits (for the base)
- 100.0 grams butter (melted for the base)
- 50.0 grams almonds (for texture in the base)

*For the raspberry topping*
- 250.0 grams raspberries (for the topping)
- 50.0 grams sugar (for the raspberry topping)
- 1.0 tablespoon lemon juice (for the raspberry topping)

**Instructions:**


*Preparation*
1. **Prepare the Oven and Cake Tin**: Preheat the oven to 160°C (300°F, gas mark 2). Grease and line a 23 cm (9 in) loose-bottomed cake tin with baking paper. _(~10 min)_

*For the base*
2. **Make the Base**: Blitz the digestive biscuits and almonds in a food processor until you have a fine crumb. Mix with melted butter. Press this mixture into the base of the lined tin to form an even layer. _(~10 min)_
3. **Bake the Base**: Bake the base in the preheated oven for 30 minutes until golden. Remove and set aside to cool. _(~30 min)_

*For the filling*
4. **Make the Filling**: Blend the cream cheese, ricotta, sugar, and salt until smooth. Mix the cornflour with lemon zest and juice, then stir well to dissolve. Beat this mixture into the cream mix, followed by the eggs one at a time until smooth. _(~15 min)_
5. **Bake the Cheesecake**: Pour the filling over the baked base. Bake in the oven for 50 minutes, then turn off the oven and leave the door open, allowing the cheesecake to cook gently in the residual heat for another 50 minutes. _(~100 min)_

*For the raspberry topping*
6. **Make the Raspberry Topping**: In a saucepan, cook the raspberries with sugar and lemon juice for about 8-10 minutes until you have a loose jam. Remove from heat, ladle off a spoonful of juice, and mix with cornflour until dissolved. Add this back to the pan and stir over heat for a minute or two until thickened. _(~15 min)_

*Serving*
7. **Cool and Serve**: Remove the cheesecake from the oven and allow to cool for at least 1 hour before serving. Top with the raspberry mixture and serve, optionally garnished with rose petals. _(~60 min)_

**Tags**: cheesecake, dessert, raspberry | **Categories**: desserts, baked goods

---

#### gpt-4o

**Provider**: OpenAI | **Latency**: 23.74s | **Cost**: $0.0141

**Title**: Cheesecake with Raspberry Cream

**Description**: A wonderfully light cheesecake made with ricotta, topped with a fresh raspberry compote.

**Servings**: 8 | **Difficulty**: medium | **Prep**: 30 min | **Cook**: 180 min | **Total**: 210 min

**Ingredients:**


*For the cheesecake*
- ricotta (mostly ricotta)
- cream cheese
- sugar
- salt
- cornflour (mixed with lemon zest and juice)
- lemon zest (mixed with cornflour)
- lemon juice (mixed with cornflour)
- eggs (added one at a time)

*For the base*
- almonds (for extra texture)
- butter (rubbed in by hand)

*For the raspberry topping*
- raspberries (cooked over low heat)
- sugar (for the raspberry topping)
- lemon juice (for the raspberry topping)
- rose essence (optional)

*For the garnish*
- rose petals (optional garnish)

**Instructions:**


*For the base*
1. **Preheat and Prepare Tin**: Preheat the oven to 160°C (300°F/gas 2). Grease and line a 9-inch loose-bottomed cake tin with baking paper. _(~10 min)_
2. **Make the Base**: Blitz the ingredients for the base together in a food processor until you have a fine crumb. Press this mixture over the base of the lined tin to form an even layer. _(~10 min)_
3. **Bake the Base**: Bake for 30 minutes until golden. Remove and set aside to cool. _(~30 min)_

*For the cheesecake*
4. **Make the Filling**: Blend the cream cheese, ricotta, sugar, and salt until smooth. Mix the cornflour with lemon zest and juice, then beat into the cream mix. Beat in the eggs, one at a time, until smooth. _(~15 min)_
5. **Bake the Cheesecake**: Pour the filling over the baked base. Bake in the oven for 50 minutes, then turn off the oven, leave the door open, and let the cheesecake cook gently in the residual heat for another 50 minutes. _(~100 min)_

*For the raspberry topping*
6. **Make Raspberry Topping**: Cook the raspberries over a low heat with lemon juice and sugar for about 8-10 minutes until you have a loose jam. Stir in cornflour dissolved in a spoonful of juice and cook for a minute or two. _(~15 min)_
7. **Cool and Serve**: Allow the raspberry mixture to cool. Stir rose essence into the raspberry mixture if desired. Top the cooled cheesecake with the raspberry topping and garnish with rose petals if desired. Chill for at least 1 hour before serving. _(~60 min)_

**Tags**: dessert, cheesecake, raspberry | **Categories**: Dessert

---

#### claude-3-5-haiku-latest

**Provider**: Anthropic | **Latency**: 15.85s | **Cost**: $0.0000

**Error**: Expecting value: line 1 column 1 (char 0)

---

### IMG_5485.HEIC

#### gemini-2.5-flash-lite

**Provider**: Google | **Latency**: 6.75s | **Cost**: $0.0005

**Title**: Malloreddus with Wild Asparagus

**Description**: One of the best ways of cooking wild asparagus that I know, here the spears are braised down to a rich, pond-green mulch into which plenty of butter and Parmesan is melted, and then used to coat pasta.

**Servings**: 2 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 30 min | **Total**: 45 min

**Ingredients:**


*For the pasta*
- 150.0 g asparagus (about 150-200 g (6-7 oz))
- 200.0 g pasta of your choice ((I use malloreddus))

*For the sauce*
- 4.0 tablespoons olive oil (or as needed)
- 1.0 small small white onion (finely sliced)
- 1.0 small dried red chilli (crumbled, or a pinch of chilli (hot pepper) flakes)
- 3.0 small sweet tomatoes (diced (optional))
- splash white wine (optional)
- 40.0 g Parmesan or pecorino (finely grated, plus extra to serve)
- 40.0 g butter

*To taste*
- to taste salt

*For the garnish*
- fresh marjoram (to garnish (optional))

**Instructions:**


*Preparation*
1. **Prepare Asparagus and Pasta Water**: Wash your asparagus well. Cut it into 2.5 cm (1 in) pieces and set any woody ends aside. Put a pot of salted water on to boil for the pasta, adding the discarded woody bits of the asparagus to flavour it. _(~5 min)_
2. **Cook Pasta**: Once boiling, fish out the asparagus ends and then drop in the pasta. Cook the pasta until it is just al dente. _(~10 min)_

*For the sauce*
3. **Sauté Aromatics and Asparagus**: Meanwhile, heat the olive oil in a sauté pan over a medium heat and sweat the onion, asparagus and chilli for a good 10-15 minutes or so, until soft and beginning to fall apart. Add a splash of water and continue to cook down, slowly, until the asparagus is almost completely soft. _(~15 min)_
4. **Add Tomatoes and Finish Sauce Base**: Add the tomatoes and cook again until everything is mushy and the asparagus is completely tender, adding a little extra oil or water if necessary (you can add a splash of white wine here, if you prefer). Taste and season with salt. _(~10 min)_

*Assembly*
5. **Combine Pasta and Sauce**: Drain the pasta, reserving a little of the cooking water. Add the butter to the sauce, along with the drained pasta and the Parmesan/pecorino. Add a little pasta cooking water and continue to cook for a minute or so, stirring gently, until the sauce is creamy and coating the pasta evenly. _(~2 min)_

*Serving*
6. **Serve**: Serve, sprinkled with extra cheese and a few marjoram sprigs (if using). _(~1 min)_

**Tags**: pasta, asparagus, vegetarian, Italian | **Categories**: Main Course, Pasta Dishes

---

#### gemini-2.0-flash

**Provider**: Google | **Latency**: 7.25s | **Cost**: $0.0007

**Title**: Malloreddus with Wild Asparagus

**Description**: One of the best ways of cooking wild asparagus. The spears are braised down to a rich, pond-green mulch into which plenty butter and Parmesan is melted, and then used to coat pasta.

**Servings**: 2 | **Difficulty**: medium | **Prep**: 10 min | **Cook**: 35 min | **Total**: 45 min

**Ingredients:**

- 175.0 g asparagus (about 150-200 g (6-7 oz))
- 200.0 g pasta (of your choice (I use malloreddus))
- 4.0 tablespoons olive oil (or as needed)
- 0.5 small white onion (finely sliced)
- 1.0 small dried red chilli (crumbled, or a pinch of chilli (hot pepper) flakes)
- 3.5 small sweet tomatoes (diced (optional))
- 1.0 splash white wine (optional)
- 40.0 g Parmesan or pecorino (finely grated, plus extra to serve)
- 40.0 g butter
- to taste salt
- fresh marjoram (to garnish (optional))

**Instructions:**

1. **Prepare the asparagus**: First wash your asparagus well. Cut it into 2.5 cm (1 in) pieces and set any woody ends aside. _(~5 min)_
2. **Cook the pasta**: Put a pot of salted water on to boil for the pasta, adding the discarded woody bits of the asparagus to flavour it. Once boiling, fish out the asparagus ends and then drop in the pasta. Cook the pasta until it is just al dente. _(~12 min)_
3. **Sauté the vegetables**: Meanwhile, heat the olive oil in a sauté pan over a medium heat and sweat the onion, asparagus and chilli for a good 10-15 minutes or so, until soft and beginning to fall apart. Add a splash of water and continue to cook down, slowly, until the asparagus is almost completely soft. Add the tomatoes and cook again until everything is mushy and the asparagus is completely tender, adding a little extra oil or water if necessary (you can add a splash of white wine here, if you prefer). Taste and season with salt _(~20 min)_
4. **Combine and serve**: Drain the pasta, reserving a little of the cooking water. Add the butter to the sauce, along with the drained pasta and the Parmesan/pecorino. Add a little pasta cooking water and continue to cook for a minute or so, stirring gently, until the sauce is creamy and coating the pasta evenly. Serve, sprinkled with extra cheese and a few marjoram sprigs (if using). _(~3 min)_

**Tags**: pasta, asparagus, italian | **Categories**: pasta dishes

---

#### gemini-2.0-flash-lite

**Provider**: Google | **Latency**: 8.57s | **Cost**: $0.0005

**Title**: Malloreddus with Wild Asparagus

**Description**: Pasta with wild asparagus, braised into a rich sauce with butter and Parmesan.

**Servings**: 2 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 35 min | **Total**: 50 min

**Ingredients:**

- 175.0 g asparagus (about)
- 200.0 g pasta of your choice ((I use malloreddus))
- 4.0 tablespoons olive oil (or as needed)
- 1.0 small white onion (finely sliced)
- 1.0 small dried red chilli (crumbled, or a pinch of chilli (hot pepper) flakes)
- 3.0 small, sweet tomatoes (diced (optional))
- white wine (splash (optional))
- 40.0 g Parmesan or pecorino (finely grated, plus extra to serve)
- 40.0 g butter

*To taste*
- salt (to taste)

*For the garnish*
- fresh marjoram (to garnish (optional))

**Instructions:**

1. **Prepare the asparagus**: Wash the asparagus well. Cut it into 2.5 cm (1 in) pieces and set any woody ends aside. _(~5 min)_
2. **Cook the pasta**: Put a pot of salted water on to boil for the pasta, adding the discarded woody bits of the asparagus to flavour it. Once boiling, fish out the asparagus ends and then drop in the pasta. Cook the pasta until it is just al dente. _(~10 min)_
3. **Sauté the vegetables**: Meanwhile, heat the olive oil in a sauté pan over a medium heat and sweat the onion, asparagus and chilli for a good 10-15 minutes or so, until soft and beginning to fall apart. Add a splash of water and continue to cook down, slowly, until the asparagus is almost completely soft. Add the tomatoes and cook again until everything is mushy and the asparagus is completely tender, adding a little extra oil or water if necessary (you can add a splash of white wine here, if you prefer). Taste and season with salt. _(~20 min)_
4. **Combine pasta and sauce**: Drain the pasta, reserving a little of the cooking water. Add the butter to the sauce, along with the drained pasta and the Parmesan/pecorino. Add a little pasta cooking water and continue to cook for a minute or so, stirring gently, until the sauce is creamy and coating the pasta evenly. Serve, sprinkled with extra cheese and a few marjoram sprigs (if using). _(~5 min)_

**Tags**: pasta, asparagus | **Categories**: Italian

---

#### gpt-4o

**Provider**: OpenAI | **Latency**: 15.36s | **Cost**: $0.0127

**Title**: Malloreddus with Wild Asparagus

**Description**: A delightful pasta dish featuring wild asparagus braised to a rich, green mulch, combined with butter and Parmesan to coat the pasta.

**Servings**: 2 | **Difficulty**: medium | **Prep**: 10 min | **Cook**: 30 min | **Total**: 40 min

**Ingredients:**


*For the pasta*
- 150.0 g asparagus (wild or cultivated, cut into 2.5 cm pieces)
- 200.0 g pasta of your choice (such as malloreddus)

*For the sauce*
- 4.0 tablespoons olive oil (or as needed)
- 1.0 small white onion (finely sliced)
- 1.0 small dried red chili (crumbled, or a pinch of chili flakes)
- 3.0 small sweet tomatoes (diced, optional)
- 1.0 splash white wine (optional)
- 40.0 g Parmesan or pecorino (finely grated, plus extra to serve)
- 40.0 g butter

*To taste*
- salt (to taste)

*For the garnish*
- fresh marjoram (to garnish, optional)

**Instructions:**


*For the pasta*
1. **Prepare asparagus**: Wash the asparagus well. Cut it into 2.5 cm (1 in) pieces and set any woody ends aside. _(~5 min)_
2. **Boil pasta**: Put a pot of salted water on to boil for the pasta, adding the discarded woody bits of the asparagus to flavor it. Once boiling, remove the asparagus ends and add the pasta. Cook until just al dente. _(~10 min)_

*For the sauce*
3. **Cook asparagus and onion**: Heat olive oil in a sauté pan over medium heat. Sweat the onion, asparagus, and chili for 10-15 minutes until soft and beginning to fall apart. Add a splash of water and continue to cook until the asparagus is almost completely soft. _(~15 min)_
4. **Add tomatoes and season**: Add the tomatoes and cook until everything is mushy and the asparagus is completely tender. Add extra oil or water if necessary. Optionally, add a splash of white wine. Taste and season with salt. _(~5 min)_
5. **Combine pasta and sauce**: Drain the pasta, reserving some cooking water. Add butter to the sauce, along with the drained pasta and Parmesan/pecorino. Add a little pasta cooking water and cook for a minute, stirring gently, until the sauce is creamy and coats the pasta evenly. _(~5 min)_

*For the garnish*
6. **Serve**: Serve the pasta sprinkled with extra cheese and a few marjoram sprigs, if using. _(~2 min)_

**Tags**: pasta, vegetarian, Italian | **Categories**: Main Course

---

#### gpt-4o-mini

**Provider**: OpenAI | **Latency**: 26.79s | **Cost**: $0.0008

**Title**: Malloreddus with Wild Asparagus

**Description**: A delicious pasta dish featuring wild asparagus braised to perfection and coated in a creamy sauce with Parmesan.

**Servings**: 2 | **Difficulty**: medium | **Prep**: 15 min | **Cook**: 30 min | **Total**: 45 min

**Ingredients:**


*For the pasta*
- 150.0 grams wild asparagus (or cultivated asparagus)
- 200.0 grams pasta (of your choice (malloreddus recommended))

*For the sauce*
- 4.0 tablespoons olive oil (or as needed)
- 1.0 piece small white onion (finely sliced)
- 1.0 piece small dried red chili (crumbled, or a pinch of chili flakes)
- 3.0 pieces small sweet tomatoes (diced (optional))
- white wine (splash (optional))
- 40.0 grams Parmesan or pecorino (finely grated, plus extra to serve)
- 40.0 grams butter

*To taste*
- salt (to taste)

*For the garnish*
- fresh marjoram (to garnish (optional))

**Instructions:**


*For the pasta*
1. **Prepare the asparagus**: Wash the asparagus well. Cut it into 2.5 cm (1 in) pieces and set any woody ends aside. _(~5 min)_
2. **Boil pasta water**: Put a pot of salted water on to boil for the pasta, adding the discarded woody bits of the asparagus to flavor it. _(~10 min)_
3. **Cook the pasta**: Once boiling, fish out the asparagus ends and then drop in the pasta. Cook the pasta until it is just al dente. _(~10 min)_

*For the sauce*
4. **Sauté the vegetables**: Meanwhile, heat the olive oil in a sauté pan over medium heat and sweat the onion, asparagus, and chili for 10-15 minutes until soft and beginning to fall apart. _(~15 min)_
5. **Cook down the mixture**: Add a splash of water and continue to cook down until the asparagus is almost completely soft. Add the tomatoes and cook until everything is mushy and the asparagus is completely tender. Season with salt. _(~10 min)_
6. **Combine pasta and sauce**: Drain the pasta, reserving a little of the cooking water. Add the butter to the sauce, along with the drained pasta and the Parmesan/pecorino. Add a little pasta cooking water and continue to cook for a minute or so, stirring gently until the sauce is creamy and coating the pasta evenly. _(~5 min)_

*For the garnish*
7. **Serve**: Serve the pasta sprinkled with extra cheese and a few marjoram sprigs if using. _(~5 min)_

**Tags**: pasta, asparagus, Italian | **Categories**: main dish

---

#### gemini-2.5-flash

**Provider**: Google | **Latency**: 11.17s | **Cost**: $0.0000

**Error**: Invalid operation: The `response.text` quick accessor requires the response to contain a valid `Part`, but none were returned. The candidate's [finish_reason](https://ai.google.dev/api/generate-content#finishreason) is 1.

---

#### claude-3-5-haiku-latest

**Provider**: Anthropic | **Latency**: 13.29s | **Cost**: $0.0000

**Error**: Expecting value: line 1 column 1 (char 0)

---
