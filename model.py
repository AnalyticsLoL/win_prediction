from transformers import AutoTokenizer, pipeline, AutoModelForSequenceClassification, TrainingArguments, Trainer
from datasets import Dataset
from langchain_core.prompts import PromptTemplate
import evaluate
import os
import time
from peft import get_peft_model, LoraConfig, TaskType

class Model:
    def __init__(self, model_name: str, checkpoint_path: str = None, model_url: str = None, isLora: bool = False):
        self.model_name = model_name
        if checkpoint_path and os.path.exists(checkpoint_path+"/"+self.model_name):
            self.load_model(checkpoint_path+"/"+(self.model_name if not isLora else self.model_name+"_lora"))
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
        vocab = champions + tiers + masteries + positions + ranks + ["win", "lose", "league", "legends", "players", "Predict", "Prediction"]

        # Add the custom tokens to the tokenizer
        self.tokenizer.add_tokens(vocab)

        self.model.resize_token_embeddings(len(self.tokenizer))
        
    def __call__(self, prompt:str):
        generator = pipeline('sentiment-analysis', model=self.model, tokenizer=self.tokenizer)
        
        return generator(prompt)
    
    def eval_model(self, testset: Dataset) -> dict:
        accuracy = evaluate.load("accuracy")
        
        predictions = []
        references = []
        for test in testset:
            predictions.append(1 if self.__call__(test["prompt"])[0]["label"] == "Win" else 0)
            references.append(test["Win"])
            
        return accuracy.compute(predictions=predictions, references=references)
    
    def tokenize_data(self, data):
        output = self.tokenizer(data["prompt"], padding="max_length", truncation=True, return_tensors="pt")
        output["input_ids"] = output["input_ids"][0]
        output['labels'] = data["Win"]
        return output
    
    def fine_tune_with_lora(self, data: Dataset):
        tokenset = data.map(self.tokenize_data)
        tokenset = tokenset.remove_columns(["token_type_ids", "Win", "prompt"])
        lora_config = LoraConfig(
            r=8,  # Rank of LoRA decomposition
            lora_alpha=32,  # Scaling factor
            lora_dropout=0.1,  # Dropout probability
            target_modules=["query", "key", "value"],  # LoRA applied to attention layers
            bias="none",
            task_type="SEQ_CLS"
        )
        
        # Apply LoRA to the model
        peft_model = get_peft_model(self.model, lora_config)
        
        output_dir = f'./checkpoints/lora/{self.model_name}_lora_{str(int(time.time()))}'
        
        peft_training_args = TrainingArguments(
            output_dir=output_dir,
            auto_find_batch_size=True,
            learning_rate=1e-6, # Higher learning rate than full fine-tuning.
            weight_decay=0.01,
            num_train_epochs=20,
            logging_steps=1,
            max_steps=20 
        )
        
        peft_trainer = Trainer(
            model=peft_model,
            args=peft_training_args,
            train_dataset=tokenset["train"],
            eval_dataset=tokenset["test"],
        )
        
        peft_trainer.train()
        
        peft_model_path=f"./checkpoints/{self.model_name}_lora"

        peft_trainer.model.save_pretrained(peft_model_path)
        self.tokenizer.save_pretrained(peft_model_path)
                
        print("LoRA fine-tuning done.")
            
            
            