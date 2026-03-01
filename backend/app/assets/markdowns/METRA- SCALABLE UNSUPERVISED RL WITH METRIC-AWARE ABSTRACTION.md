# Level 1 – Absolute beginner

## Why this paper matters

This paper introduces a new method called METRA (Metric-Aware Abstraction) for unsupervised reinforcement learning (RL). METRA aims to make unsupervised RL scalable to complex, high-dimensional environments by focusing on covering a compact latent space that is connected to the state space by temporal distances. This approach helps in discovering diverse behaviors that can be useful for various downstream tasks, even in challenging environments like pixel-based locomotion and manipulation tasks.

## High-level idea in everyday language

Imagine you are exploring a new city without a map. Instead of trying to visit every single street (which would be impossible), you decide to explore the main areas and landmarks. METRA does something similar in the world of AI. It focuses on exploring the most important parts of a complex environment, rather than trying to cover every single detail. This makes it more efficient and scalable.

## Simple example to illustrate it

Think of a robot learning to walk in a room. Instead of trying to learn every possible way to move its legs, METRA helps the robot focus on the most important movements, like walking forward, backward, and turning. This way, the robot can learn to navigate the room more efficiently.

## What this research could be used for

METRA could be used to train AI agents in complex environments without the need for specific tasks or rewards. This could be useful in areas like robotics, where agents need to learn a wide range of behaviors to be effective. For example, a robot could learn to navigate different terrains or manipulate objects without being explicitly told how to do so.

## One important limitation or caveat

One limitation of METRA is that it might not capture all possible behaviors, especially in very complex environments. This is because it focuses on the most important behaviors, which might not include some rare or unusual actions.

## Reference

**Seohong Park, Oleh Rybkin, Sergey Levine**

University of California, Berkeley

seohong@berkeley.edu

Published as a conference paper at ICLR 2024