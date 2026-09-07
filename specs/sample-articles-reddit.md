# Summary

Initial prompt for ChatGPT and Claude

## Links to reddit (from conversation)

https://www.reddit.com/r/StrixHalo/s/ISGWi1Hsxq
https://www.reddit.com/r/StrixHalo/s/mx91oKNehn
https://www.reddit.com/r/LocalLLaMA/s/b6I9LASbBD
https://www.reddit.com/r/StrixHalo/s/Gi4zVkXm7h
https://www.reddit.com/r/StrixHalo/s/9urzxgC0PS
https://www.reddit.com/r/LocalLLaMA/s/VCPK6GUHP9
https://www.reddit.com/r/StrixHalo/s/h7mNyzuQXv
https://www.reddit.com/r/StrixHalo/s/fVSzxl1OJP
https://www.reddit.com/r/StrixHalo/s/2C8p16o5XC



## Prompt

Here what I want to build, you have me great ideas on how to represent all in the format, what methods to add etc

I have a strix halo 128gb unified memory processor. Cachyos 110gb freed to run models
I have it running Qwen 3.5, GLM 1.2
Now I want to try Qwen 3.8, next and possible DeepSeek V4

Now I find plenty of online posts all made by ai testing different quants, mtp, context sizes etc

For me it's irrelevant to have a chat if the model cannot work with a harness it's potential is wasted, so it should be able to use skills, MCPs, tools and have vision. I know this is added later in an easy way mmproj, but it should be part of the spec so models can see what they are building. Or at least one of the options

I use for example oh my pi, omp, a variant of Pi with useful extras but easy to configure. You helped me set up that machine and as llama was not visible you implemented a layer that exposes llama-swap models pretending to be lm studio (that was the only way) 

Anyway, we also made a guide on how to investigate the system memory, models, llama version, specific model etc

Let me give you a few examples of how people share

https://www.reddit.com/r/StrixHalo/s/ISGWi1Hsxq
https://www.reddit.com/r/StrixHalo/s/mx91oKNehn
https://www.reddit.com/r/LocalLLaMA/s/b6I9LASbBD
https://www.reddit.com/r/StrixHalo/s/Gi4zVkXm7h
https://www.reddit.com/r/StrixHalo/s/9urzxgC0PS
https://www.reddit.com/r/LocalLLaMA/s/VCPK6GUHP9
https://www.reddit.com/r/StrixHalo/s/h7mNyzuQXv
https://www.reddit.com/r/StrixHalo/s/fVSzxl1OJP
https://www.reddit.com/r/StrixHalo/s/2C8p16o5XC

Anyway, all those posts are clearly agent driven and very hard to replicate 

What I want to do is 
- create a script that collects all setup data (can be Linux only) 
- define a format that defines all setup data, models, flags, tests, validated by other people, other people results
- create a skill so agents know how to pull the data and how you contribute 

At it's heart, it will be a collection of recipes with lineage

So other users can just tell the agent to replicate a recipe and they can test immediately
The agent can then  run tests, submit testing data, results etc

The format is perhaps they most crucial part so it's extendable in the future and it carries enough information

Bad runs and failures should also be added so agents can learn quickly

The repo should also contain tools for easy searching the recipes, so the agents don't spend million tokens going through 100s of recipes (eventually). This is basic search in JSON so not very hard,

We also need to maintain a list of models we're testing, and we could have summarize scripts that maintain a leaderboard (perhaps) 

How many people have run a recipe successfully, what scores they got are critical, we cannot trust a new commit add the winner if never tested. The whole thing is stored on git

And you be honest this is not very hard, ice done similar things with agents and multiple users for my previous work 

We can use python or node or bash

Can you go over this and help me define the instruments we need, a good format, and recipe versioning with lineage (multiple allowed) we can define in front matter so perhaps we take two recipes and combine 
