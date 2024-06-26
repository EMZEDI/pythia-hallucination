# MIND: Unsupervised Hallucination Detection Framework for LLMs



**📢 News: this work has been accepted at the Findings of ACL 2024!**

**If you find our project interesting or helpful, we would appreciate it if you could give us a star! Your support is a tremendous encouragement to us!**



Welcome to the official GitHub repository for our latest research on hallucination detection in Large Language Models (LLMs), titled **"MIND: Unsupervised Modeling of Internal States for Hallucination Detection of Large Language Models"**. In this work, we introduce a novel, unsupervised framework designed to address the challenges of existing hallucination detection methods. 



If you have any questions or need further clarification, please feel free to open an issue in this repository. We are happy to assist and will respond as quickly as possible.





## Overview

Our research highlights the limitations of current post-processing methods used in hallucination detection, including their high computational costs, latency, and inability to understand how hallucinations are generated within LLMs. To overcome these challenges, we propose **MIND**, an unsupervised and real-time hallucination detection framework that significantly reduces computational overhead and detection latency, and is compatible with any Transformer-based LLM.

**MIND** extracts pseudo-training data directly from Wikipedia, eliminating the need for manual annotation, and uses a simple multi-layer perceptron model to perform hallucination detection during the LLM's inference process.

![](pics/framework.png)

## Benchmark: HELM

To further contribute to the field, we introduce a new benchmark named **HELM (Hallucination Evaluation for multiple LLMs)**, aimed at improving the reproducibility of our findings and facilitating future research. Unlike previous benchmarks, HELM provides texts produced by six different LLMs along with human-annotated hallucination labels, contextualized embeddings, self-attentions, and hidden-layer activations. This comprehensive dataset offers invaluable insights into the internal states of LLMs during the inference process.



### Data Release

The  `./HELM`  folder contains our HELM dataset, including content generated by LLM, the internal states during LLM content generation, and a Hallucination Label.

`./helm/data/{model_name}/data.json`: Data for each model. The model continues writing based on prompts related to the wikipedia data. The data is generated by greedy search. 

The key in the file is the ID of the wiki passage related to Helm (we provide a unique ID for passages related to Helm). The value is a dictionary: The `prompt` field represents the prompt provided to the LLM, corresponding to `./helm/prompt_mapping.txt`. The `sentences` field contains a list of sentences generated by each model (arranged in the order in which they were generated). The elements in the list contain two fields: the `sentence` field represents the continued sentence, and the `label` field represents the human annotation of hallucination, where 1 indicates hallucination and 0 indicates no hallucination. 



`./helm/prompt_mapping.txt`: Each line follows the format:

```
{wiki_helm_id}: {prmopt}
```

`./helm/hd/{model_name}/hd.json`: Internal states of the model when generating Helm data. The key in the file is the ID of the wiki passage related to Helm (matching the IDs in `data.json`). The value is a dictionary: the `sentences` field is a list, where the elements correspond one-to-one with the sentences in the `sentences` field in `data.json`, representing the internal states of the model when generating that sentence. The `passage` field represents the internal states  when generating the entire passage.

The format of internal states is as follows:

```
{
    "hd_last_token": Hidden states of the last token (mean pooling across all layers),
    "hd_last_mean": Mean pooling of the hidden states (in the last layer) of the generated token,
    "probability": List of probabilities when generating each token,
    "entropy": List of entropies when generating each token
}
```

`./helm/hd/{model_name}/hd_act.json`: The activation value of the model when generating Helm data. The data organization is similar to that of `hd_json`.

The format of internal states is as follows:

```
{
    "activition": Activation of the last layer of the last token
}
```



### Data Generation Process

#### Sentences
We provide prompts to LLMs as shown in `prompt_mapping.txt`. The generation settings are as follows:
```
generation_config = dict(
                        top_k=0,
                        top_p=1.0,
                        do_sample=False,
                        num_beams=1,
                        max_new_tokens=128,
                        return_dict_in_generate=True,
                    )
```

#### Internal states
You can run `generate_hd_for_helm.py` and obtain the same data as `./helm/hd/{model_name}/hd.json`.


## Repository Content

In this repository, we provide:

- Complete source code for the **MIND** framework.

- Instructions for setting up and running **MIND**.

- Access to the **HELM** benchmark, including detailed documentation on how to use it for your own research.

  

## Getting Started

### Requirements

```
numpy==1.25.2
pandas==2.0.3
scikit_learn==1.3.0
spacy==3.6.1
torch==2.0.1
tqdm==4.66.1
transformers==4.31.0
```



### Install Environment

```bash
conda create -n MIND python=3.9
conda activate MIND
pip install torch==2.0.1
pip install -r ./requirements.txt
```



### Step 1

**Run `./generate_data.py` to automatically annotate the dataset based on wiki data.** You can modify hyperparameters, paths, model names, and sizes in the file.

You will get three files at `output_path` (default is `./auto-labeled/output/{model_name}/data_{datasplit}.json`), where `datasplit` is train, valid or test. These files contain the original data for each wiki sentence, the hallucinated data generated by the model, in the following format:

```
{
    "original_text": Original sentence sampled from Wikipedia,
    "title": Title of the corresponding Wikipedia article,
    "texts": List of hallucinated sentences generated by the model (hallucinated parts marked with @@),
    "new_entities": Corresponding to the "texts" field, a list of strings where the model has predicted the original entity as a new hallucinated string,
    "original_entities": Corresponding to the "texts" field, each element is a list where the first element refers to the original entity that was replaced, and the second element refers to the starting index (as a Python string) of that entity in "original_text"
}
```



### Step 2

**Run `generate_hd.py` to generate features needed for training the classifier based on the automatically annotated data.**

You will get six files at `result_path` (default is `./auto-labeled/output/{model_name}/last_token_mean_{data_type}.json` and `./auto-labeled/output/{model_name}/last_mean_{data_type}.json`), where `datasplit` is train, valid or test. The former contains hidden states of the last token (mean pooling across all layers) and the latter contains mean pooling of the hidden states (in the last layer) of all the tokens.

Each file contains a list, and the elements of the list are dictionaries as follows:

```
{
    "right": The hidden states of the original sentence, 
    "hallu": List of the hidden states of each hallucinated sentence generated from the original sentence
}
```



### Step 3

**Run `./auto-labeled/train/train.py` to train the classifier.**

For example, if you train a classifier using the default parameters for `llamabase7b`, you will get the following output (omitting the intermediate outputs):

```
train data: [0, 1] - [2658, 2658]
valid data: [0, 1] - [475, 475]
...
Train Epoch 20 end ! Loss : 64.84507662057877; Train Acc: 0.8028592927012792
Valid Epoch 20 ...
Best acc : 0.7210526315789474 from epoch 14th;
llamabase7b
```



### Step 4

**Run `./detection_score.py` to evaluate the classifier's performance on the HELM dataset.**

You can modify the code to evaluate different models. For example, if you use the default model (i.e., llamabase7b) in the above steps and have not generated data for other models yet, you can add the following line of code after `model = sorted(model)`:

```python
model = ["llamabase7b"]
```

After running the code, you will obtain `result_psg_corr.xlsx`, `result_psg_halu.xlsx`, `result_sent_corr.xlsx`, and `result_sent_halu.xlsx` at the specified path, representing the correlation coefficients at the passage level, hallucination evaluation performance (using AUC as the metric) at the passage level, and the correlation coefficients at the sentence level, as well as hallucination evaluation performance (using AUC as the metric) at the sentence level.

The results presented in `result_sent_halu.xlsx` are as follows:

|             | Our_score   |
| ----------- | ----------- |
| llamabase7b | 78.76393327 |
