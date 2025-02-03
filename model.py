from transformers import AutoTokenizer, AutoModelForMaskedLM, pipeline, AutoModelForSequenceClassification
import os

class Model:
    def __init__(self, model_name: str, checkpoint_path: str = None, model_url: str = None):
        self.model_name = model_name
        if checkpoint_path and os.path.exists(checkpoint_path+"/"+self.model_name):
            self.load_model(checkpoint_path+"/"+self.model_name)
        elif model_url:
            self.load_model(model_url)
            self.update_tokenizer()
        else:
            raise ValueError("Please provide a model url or a checkpoint path")
    
    def load_model(self, path):
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        id2label = {0: "Lose", 1: "Win"}
        label2id = {"Lose": 0, "Win": 1}
        self.model = AutoModelForSequenceClassification.from_pretrained(path,
                                                                        num_labels=len(id2label),
                                                                        id2label=id2label,
                                                                        label2id=label2id)
        
    def save_model(self, path):
        self.tokenizer.save_pretrained(path+"/"+self.model_name)
        self.model.save_pretrained(path+"/"+self.model_name)
        print(f"Model saved at {path}/{self.model_name}")
        
    def update_tokenizer(self):
        champions = [f"champion_{str(i)}" for i in [266, 103, 84, 166, 12, 799, 32, 34, 1, 523, 22, 136, 893, 268, 432, 200, 53, 63, 201, 233, 51, 164, 69, 31, 42, 122, 131, 119, 36, 245, 60, 28, 81, 9, 114, 105, 3, 41, 86, 150, 79, 104, 887, 120, 74, 910, 420, 39, 427, 40, 59, 24, 126, 202, 222, 145, 429, 43, 30, 38, 55, 10, 141, 85, 121, 203, 240, 96, 897, 7, 64, 89, 876, 127, 236, 117, 99, 54, 90, 57, 11, 800, 902, 21, 62, 82, 25, 950, 267, 75, 111, 518, 76, 895, 56, 20, 2, 61, 516, 80, 78, 555, 246, 133, 497, 33, 421, 526, 888, 58, 107, 92, 68, 13, 360, 113, 235, 147, 875, 35, 98, 102, 27, 14, 15, 72, 901, 37, 16, 50, 517, 134, 223, 163, 91, 44, 17]]
        tiers = [f"tier_{tier}" for tier in ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]]
        ranks = ["rank_IV", "rank_III", "rank_II", "rank_I"]
        masteries = [f"mastery_{i}" for i in range(0, 101)]
        positions = ["TOP", "MIDDLE", "BOTTOM", "JUNGLE", "UTILITY"]

        # Combine everything into a vocabulary
        vocab = champions + tiers + masteries + positions + ranks + ["win", "lose"]

        # Add the custom tokens to the tokenizer
        self.tokenizer.add_tokens(vocab)

        self.model.resize_token_embeddings(len(self.tokenizer))
        
    def __call__(self, prompt:str):
        generator = pipeline('sentiment-analysis', model=self.model, tokenizer=self.tokenizer)
        
        return generator(prompt)