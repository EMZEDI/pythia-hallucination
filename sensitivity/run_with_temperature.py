from most_sensitive import *
import warnings

# Suppress specific PyTorch warning about TypedStorage
warnings.filterwarnings("ignore", message="TypedStorage is deprecated")

def run_with_temperature_concat(accelerator, model_name, input_text, temperature=0.5, contextual_embedding_extraction_form="last_token", middle=False):
    """Generates the embedding matrix of 10 concatenated texts of input and an output generated by the model with the given input text for the EigenScore analysis.

    Args:
        accelerator (_type_): _description_
        model_name (_type_): _description_
        input_text (_type_): _description_
        temperature (float, optional): _description_. Defaults to 0.5.
        contextual_embedding_extraction_form (str, optional): _description_. Defaults to "last_token".
        middle (bool, optional): _description_. Defaults to True.

    Returns:
        _type_: _description_
    """
    REVISION = 143000
    model = GPTNeoXForCausalLM.from_pretrained(model_name, revision=f"step{REVISION}", device_map='auto')
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=f"step{REVISION}")
    model, tokenizer = accelerator.prepare(model, tokenizer)

    concatenated_texts = []
    current_input = input_text

    inputs = tokenizer(current_input, return_tensors="pt")
    input_ids = inputs.input_ids.to(accelerator.device)
    attention_mask = inputs.attention_mask.to(accelerator.device)

    for _ in range(10):
        output = model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=64, temperature=temperature, do_sample=True, top_k=5, top_p=0.99)
        generated_text = tokenizer.decode(output[0])
        current_input += generated_text

        concatenated_texts.append(current_input)

    input_ids = input_ids.cpu()
    attention_mask = attention_mask.cpu()
    del input_ids, attention_mask

    embeddings = []
    for text in concatenated_texts:
        inputs = tokenizer(text, return_tensors="pt")
        tokens = inputs.input_ids.to(accelerator.device)
        attention_mask = inputs.attention_mask.to(accelerator.device)
        with torch.no_grad():
            outputs = model(tokens, attention_mask=attention_mask, output_hidden_states=True)
            if middle:
                penultimate_embeddings = outputs.hidden_states[len(outputs.hidden_states) // 2]
            else:
                penultimate_embeddings = outputs.hidden_states[-2]
            if contextual_embedding_extraction_form == "SLT":
                embeddings.append(penultimate_embeddings[:, -2, :])
            elif contextual_embedding_extraction_form == "pooled":
                embeddings.append(penultimate_embeddings.mean(dim=1))
            elif contextual_embedding_extraction_form == "last_token":
                embeddings.append(penultimate_embeddings[:, -1, :])

    embeddings = np.concatenate([embedding.cpu() for embedding in embeddings], axis=0)
    
    return embeddings

def run_with_temperature(accelerator, model_name, input_text, temperature=0.5, contextual_embedding_extraction_form="last_token", middle=False):
    """Generates the embedding matrix of 10 different outputs of inference with temperature.

    Args:
        accelerator (_type_): _description_
        model_name (_type_): _description_
        input_text (_type_): _description_
        temperature (float, optional): _description_. Defaults to 0.5.
        contextual_embedding_extraction_form (str, optional): _description_. Defaults to "last_token".
        middle (bool, optional): _description_. Defaults to True.

    Returns:
        _type_: _description_
    """
    REVISION = 143000
    model = GPTNeoXForCausalLM.from_pretrained(model_name, revision=f"step{REVISION}", device_map='auto')
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=f"step{REVISION}")
    model, tokenizer = accelerator.prepare(model, tokenizer)

    outputs = []

    inputs = tokenizer(input_text, return_tensors="pt")
    input_ids = inputs.input_ids.to(accelerator.device)
    attention_mask = inputs.attention_mask.to(accelerator.device)

    for _ in range(10):
        output = model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=128, temperature=temperature, do_sample=True, top_k=5, top_p=0.99)
        generated_text = tokenizer.decode(output[0])

        outputs.append(generated_text)

    input_ids = input_ids.cpu()
    attention_mask = attention_mask.cpu()
    del input_ids, attention_mask

    embeddings = []
    for text in outputs:
        inputs = tokenizer(text, return_tensors="pt")
        tokens = inputs.input_ids.to(accelerator.device)
        attention_mask = inputs.attention_mask.to(accelerator.device)
        with torch.no_grad():
            outputs = model(tokens, attention_mask=attention_mask, output_hidden_states=True)
            if middle:
                penultimate_embeddings = outputs.hidden_states[len(outputs.hidden_states) // 2]
            else:
                penultimate_embeddings = outputs.hidden_states[-2]
            if contextual_embedding_extraction_form == "SLT":
                embeddings.append(penultimate_embeddings[:, -2, :])
            elif contextual_embedding_extraction_form == "pooled":
                embeddings.append(penultimate_embeddings.mean(dim=1))
            elif contextual_embedding_extraction_form == "last_token":
                embeddings.append(penultimate_embeddings[:, -1, :])

    embeddings = np.concatenate([embedding.cpu() for embedding in embeddings], axis=0)
    
    return embeddings

if __name__ == '__main__':
    accelerator = Accelerator()
    model_name = "EleutherAI/pythia-70m"
    input_text = "Continue this: The quick brown fox jumps over the lazy dog "
    embeddings = run_with_temperature(accelerator, model_name, input_text)
