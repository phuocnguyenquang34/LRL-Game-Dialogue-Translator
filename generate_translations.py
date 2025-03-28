from collections import defaultdict
import os
from tqdm import tqdm
from utils import *
from translator import *

translator_class_list = GameDialogueTranslator.__subclasses__()
samples = create_dataset(num_samples_each_depth=50)
lang_list = ["Vietnamese", "Portuguese", "Bengali", "Spanish"]

save_dir = 'output'
os.makedirs(save_dir, exist_ok=True)

for language in lang_list:
    print(f"_____________Language {language}")
    results = defaultdict(dict)
    
    # Iterate through each subclass in the translator class list
    for subclass in tqdm(translator_class_list):
        variation_list = subclass.get_possible_variations()
        
        for variation in tqdm(variation_list):
            total_time = 0
            total_gpu_cost = 0
            variation_result = defaultdict(dict)
            
            print(f"_____Working on {variation}")
            
            # Attempt to initialize the translator with system_prompt if required
            try:
                translator = subclass(variation=variation, system_prompt=system_prompt)
            except TypeError:
                # For translators that don't require the system_prompt (e.g., NLLB, Bloomz, mT0)
                translator = subclass(variation=variation)
            
            # Translate each selected example
            for sample in tqdm(samples):
                original_game_dialogue = sample['dialogue_tree']
                
                # Start timing the translation
                translation, time_cost, gpu_cost = translator.translate_text(original_game_dialogue, target_lang=language)
                clean_gpu()
                total_time += time_cost
                total_gpu_cost += gpu_cost
                
                # Save the result
                variation_result[original_game_dialogue] = translation
            
            # Calculate the mean time cost
            variation_result['mean_time_cost'] = total_time / len(samples)
            variation_result['mean_gpu_cost'] = total_gpu_cost / len(samples)
            
            # Append the result for this variation
            results[variation] = variation_result
            
            del translator.model
            clean_gpu()
            print(f"Example: \n{original_game_dialogue} \n\n{translation}")

    df = pd.DataFrame(results).T
    df.to_csv(f"{save_dir}/{language.lower()}_game_translation_{len(samples)}.csv")