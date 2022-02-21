# Bridging Textual and Tabular Data for Cross-Domain Text-to-SQL Semantic Parsing

***
**02/10/2022**

This repository is a fork of the [official release](https://github.com/salesforce/TabularSemanticParsing).
The objective of this repository is to make it possible to deploy the original model into a server, so it can be used 
to respond queries made by other applications (i.e. translate natural language texts into SQL statements, and also 
return the result of the SQL queries executed in a database). 

In our use case, this server is used to help chatbots of the
[bodi-generator](https://github.com/opendata-for-all/bodi-generator) project answer natural language 
questions by executing their respective SQL translations into databases made up by .csv files.

The server that deploys this model can be found at
[opendata-for-all/bodi-nlp-server](https://github.com/opendata-for-all/bodi-nlp-server)

***

This is (not) the official code release of the following paper:

Xi Victoria Lin, Richard Socher and Caiming Xiong. [Bridging Textual and Tabular Data for Cross-Domain Text-to-SQL Semantic Parsing](https://arxiv.org/abs/2012.12627). Findings of EMNLP 2020.

## Overview

Cross-domain tabular semantic parsing (X-TSP) is the task of predicting the executable structured query language given a natural language question issued to some database. The model may or may not have seen the target database during training.

This library implements 
- A strong sequence-to-sequence based cross-domain text-to-SQL semantic parser that achieved state-of-the-art performance on two widely used benchmark datasets: [Spider](https://yale-lily.github.io/spider) and [WikiSQL](https://github.com/salesforce/WikiSQL). 
- A set of [SQL processing tools](moz_sp) for parsing, tokenizing and validating SQL queries, adapted from the [Moz SQL Parser](https://github.com/mozilla/moz-sql-parser).

The parser can be adapted to learn mappings from text to other structured query languages such as [SOQL](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql.htm) by modifying the formal langauge pre-processing and post-processing modules.

## Model

![BRIDGE architecture](http://victorialin.net/img/bridge_architecture.png)

Our model takes a natural language utterance and a database (schema + field picklists) as input, and generates SQL queries as token sequences. We apply schema-guided decoding and post-processing to make sure the final output is executable.
- **Preprocessing:** We concatenate the serialized database schema with the utterance to form a tagged sequence. A [fuzzy string matching algorithm](src/common/content_encoder.py) is used to identify picklist items mentioned in the utterance. The mentioned picklist items are appended to the corresponding field name in the tagged sequence.
- **Translating:** The hybrid sequence is passed through the BRIDGE model, which output raw program sequences with probability scores via beam search.
- **Postprocessing:** The raw program sequences are passed through a SQL checker, which verifies its syntactical correctness and schema consistency. Sequences that failed to pass the checker are discarded from the output.

## Quick Start

### Install Dependencies

Our implementation has been tested using Pytorch 1.7 and Cuda 11.0 with a single GPU.
```
git clone https://github.com/mgv99/TabularSemanticParsing
cd TabularSemanticParsing

pip install torch torchvision
python3 -m pip install -r requirements.txt
```

### Set up Environment
```
export PYTHONPATH=`pwd` && python -m nltk.downloader punkt
```

## Pre-trained Checkpoints

#### Spider
Download pre-trained checkpoint here:
<table>
   <tr>
      <td><strong>URL</strong></td>
      <td><strong>E-SM</strong></td>
      <td><strong>EXE</strong></td>
   </tr>
   <tr>
      <td>https://drive.google.com/file/d/1dlrUdGMLvvvfR3kNVy76H12rR7gr4DXI/view?usp=sharing</td>
      <td>70.1</td>
      <td>68.2</td>
   </tr>
</table>

```
mv bridge-spider-bert-large-ems-70-1-exe-68-2.tar.gz model
gunzip model/bridge-spider-bert-large-ems-70-1-exe-68-2.tar.gz
```
(There are other checkpoints available in the original repository, but since we have only tested this one, we 
recommend using it)

## Citation
If you find the resource in this repository helpful, please cite
```
@inproceedings{LinRX2020:BRIDGE, 
  author = {Xi Victoria Lin and Richard Socher and Caiming Xiong}, 
  title = {Bridging Textual and Tabular Data for Cross-Domain Text-to-SQL Semantic Parsing}, 
  booktitle = {Proceedings of the 2020 Conference on Empirical Methods in Natural
               Language Processing: Findings, {EMNLP} 2020, November 16-20, 2020},
  year = {2020} 
}
```

## Related Links
The parser has been integrated in the Photon web demo: http://naturalsql.com/. Please visit our website to test it live and try it on your own databases!
