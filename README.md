# Better Ways of Thinking About Software

Series of talks at OSOCO about other (better?) ways of thinking about software.

This is a work in progress. It would be updated as new talks and workshops were celebrated at OSOCO.

## Contents of this repo

  * [Introduction to the series](https://osoco.github.io/better-ways-of-thinking-about-software/)
  * Part 1: Introduction to Model Checking with TLA+:
     * [Slides](https://osoco.github.io/better-ways-of-thinking-about-software/Part-01-Introduction-TLA+/slides/formal-specifications.html)
     * [TLA+ sources for exercises](Part-01-Introduction-TLA+/sources)
  * Part 2: Beyond Lines of Code (TBD).
  * Part 3: Understanding Software by Crafting Your Own Tools:
     
     * Install [Glamorous Toolkit](https://gtoolkit.com) and load the presentation and demos of Part 3 evaluating the following expressions in a Playground:
     
     
``` smalltalk
  Metacello new
    repository: 'github://osoco/better-ways-of-thinking-about-software/src';
    baseline: 'CraftingToolsForUnderstandingSoftware';
    load.
```
    
    After the loading has completed, you can proceed to load the Lepiter contents evaluating this statement:
   
``` smalltalk
    BaselineOfCraftingToolsForUnderstandingSoftware loadLepiter
```


    
    


