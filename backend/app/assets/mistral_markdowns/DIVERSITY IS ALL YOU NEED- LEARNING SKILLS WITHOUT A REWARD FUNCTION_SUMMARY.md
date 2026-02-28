## Diversity is All You Need: Learning Skills Without a Reward Function

This work introduces **DIAYN** (*Diversity Is All You Need*), a framework for **unsupervised skill discovery** in reinforcement learning (RL) that learns a diverse set of behaviors *without* requiring an extrinsic reward function. Instead of relying on handcrafted rewards, DIAYN trains a **policy** (an agent’s decision-making model) to maximize the mutual information between **skills** (distinct behaviors) and **achieved states** (outcomes in the environment). The core idea is to incentivize the agent to explore a wide range of behaviors by ensuring each skill leads to *diverse and distinguishable* outcomes.

### Key Concepts
- **Unsupervised Skill Learning**: The agent learns reusable behaviors (e.g., walking, jumping) autonomously, without task-specific rewards. This contrasts with traditional RL, where rewards are manually designed for each task.
- **Mutual Information Maximization**: The framework encourages the policy to produce states that are *predictable* from the skill identifier (a latent variable) while ensuring different skills lead to *distinct* states. This is achieved by:
  - **Skill Conditioning**: The policy takes a *skill vector* (a latent code) as input, producing different behaviors for different codes.
  - **Discriminator Network**: A separate network predicts the skill from the resulting state, acting as a proxy for mutual information. The policy is rewarded for making this prediction *easy* (high mutual information) while the discriminator is trained to improve its accuracy.

- **Diversity as Intrinsic Motivation**: By maximizing diversity, the agent avoids collapsing into a single behavior and instead explores a broad repertoire of skills, which can later be repurposed for downstream tasks.

### Method Overview
1. **Policy Training**: The agent’s policy π(a|s, z) is conditioned on both the environment state *s* and a skill latent *z* (sampled from a prior distribution, e.g., Gaussian). The goal is to maximize the mutual information *I*(z; s′), where *s′* is the next state.
2. **Discriminator Training**: A discriminator *q*(z|s′) is trained to infer the skill *z* from the resulting state *s′*. The policy is rewarded based on the discriminator’s confidence (log *q*(z|s′)), effectively pushing the policy to generate states that are *uniquely identifiable* by their skill.
3. **Regularization**: A term is added to prevent the discriminator from trivially solving the task (e.g., by ignoring *s′*), ensuring the policy must actually produce diverse behaviors.

### Advantages
- **Task-Agnostic Learning**: Skills are learned without prior knowledge of tasks, enabling zero-shot transfer to new environments.
- **Scalability**: The approach avoids the need for reward engineering, which is often labor-intensive and domain-specific.
- **Reusability**: Discovered skills can be composed or fine-tuned for complex downstream tasks, such as hierarchical RL or multi-task learning.

### Experimental Validation
DIAYN was evaluated in **MuJoCo** and **PyBullet** environments, demonstrating:
- **Diverse Skill Repertoires**: Agents learned distinct behaviors (e.g., running forward/backward, spinning) in locomotion tasks, visualized via t-SNE embeddings of states.
- **Downstream Task Performance**: Pre-trained skills improved sample efficiency when fine-tuned for specific goals (e.g., reaching targets).
- **Comparison to Baselines**: Outperformed methods like **variational intrinsic control (VIC)** and **state marginal matching**, which often produced less diverse or collapsed behaviors.

---
*[∗] Work conducted while at Google Brain.*

## ABSTRACT

**"Diversity is All You Need" (DIAYN)** is an unsupervised learning framework that enables agents to autonomously discover useful skills *without external rewards*. The method leverages **maximum entropy reinforcement learning** to maximize a diversity-driven objective, encouraging the agent to explore a wide range of behaviors.

Key contributions:
- **Unsupervised skill discovery**: By optimizing an _information-theoretic objective_, DIAYN learns diverse behaviors (e.g., walking, jumping) in simulated robotic tasks—*without task-specific rewards*.
- **Benchmark performance**: On standard reinforcement learning (RL) tasks, DIAYN’s pretrained skills often solve the intended task *despite never receiving the true reward signal*.
- **Pretraining for efficiency**: Learned skills serve as effective **parameter initializations** for downstream tasks, improving exploration and data efficiency.
- **Hierarchical composition**: Skills can be combined to solve complex, **sparse-reward** problems, demonstrating scalability.

The results suggest that unsupervised skill learning could address key challenges in RL, such as **exploration bottlenecks** and **sample inefficiency**.

## 1 INTRODUCTION

Deep reinforcement learning (RL) has achieved success in training agents to perform complex tasks—such as playing games (e.g., Atari, Go), controlling robots, and navigating environments—when provided with explicit **reward signals**. However, intelligent agents in nature often explore and acquire skills *without* external supervision, enabling rapid adaptation when goals are later introduced. This paper addresses the challenge of **unsupervised skill discovery**: learning a diverse set of behaviors in the absence of rewards, which can later be repurposed for hierarchical RL, exploration, or imitation learning.

### Key Motivations
Unsupervised skill learning offers practical advantages:
- **Sparse rewards**: Agents can pre-learn useful behaviors to overcome exploration challenges in environments where rewards are rare or delayed.
- **Long-horizon tasks**: Discovered skills can act as **primitives** for hierarchical RL, reducing the effective episode length.
- **Reduced human supervision**: Skills learned without rewards minimize the need for manual reward design or human feedback (e.g., in inverse RL).
- **Generalization**: Pre-learned skills help agents adapt quickly to unfamiliar tasks or environments.

### Core Problem
The goal is to autonomously learn a set of **skills**—defined as *latent-conditioned policies* that consistently alter the environment’s state—**without any reward signal**. The challenge lies in designing an objective that ensures:
1. **Distinctness**: Each skill must behave differently (e.g., avoid redundant "random dithering").
2. **Diversity**: Skills should cover a broad, *semantically meaningful* range of behaviors (e.g., running, jumping, backflipping), not just trivial variations.
3. **Robustness**: Skills should be resilient to perturbations and explore the state space effectively.

### Proposed Solution
The authors introduce a method that frames skill diversity as an **information-theoretic objective**, combining:
- **Mutual information**: Maximizes the dependency between skills and their outcomes, ensuring distinguishability.
- **Maximum entropy**: Encourages exploration, pushing skills to be as diverse and "random" as possible while remaining controlled. This objective leads to the emergence of complex, interpretable behaviors (e.g., locomotion, acrobatics) without explicit rewards.

![Diverse skills learned by the agent, including running, backflipping, and face-planting](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-2.png)

### Contributions
The paper presents five key advances:
1. A **theoretical framework** for unsupervised skill learning using mutual information and entropy maximization.
2. **Empirical validation**: The method autonomously discovers diverse skills (e.g., running, jumping) in simulated robotic tasks, even solving benchmark RL environments *without ever receiving task rewards*.
3. **Hierarchical RL integration**: A simple method to leverage learned skills for solving complex, long-horizon tasks.
4. **Fast adaptation**: Demonstrates how pre-learned skills can be quickly fine-tuned for new tasks.
5. **Imitation learning**: Shows that discovered skills can be repurposed for mimicking expert behaviors.

## 2 Related Work

### **Hierarchical Reinforcement Learning (HRL)**
Prior HRL methods learn **skills** (low-level policies) and a **meta-controller** (high-level policy) to maximize a *known* reward function (e.g., Bacon et al., 2017; Florensa et al., 2017). A key limitation is that the meta-policy avoids "bad" skills, starving them of learning signals. This work addresses this by:
- Using a **random meta-policy** during unsupervised skill learning, ensuring no bias toward specific tasks.
- Learning skills **without any reward function**, enabling task-agnostic skill discovery and avoiding manual reward design.

### **Information Theory in RL**
Research has linked RL to **information theory**, using **mutual information (MI)** to quantify empowerment (Mohamed & Rezende, 2015) or intrinsic motivation (Jung et al., 2011). This work extends these ideas by:
- Maximizing MI between **states and skills** (not actions), interpreting this as empowering a *hierarchical agent* whose actions are high-level skills.
- Building on discriminability objectives (Hausman et al., 2018; Florensa et al., 2017) but improving scalability via:
  1. **Maximum entropy policies**: Ensures skill diversity; theoretical analysis shows this leads to aggregate maximum entropy.
  2. **Fixed prior over skills**: Prevents collapse to a few dominant skills.
  3. **State-level discrimination**: The discriminator evaluates *every state* (not just final states), providing richer learning signals.

These advances enable learning in complex environments beyond simple gridworlds (Gregor et al., 2016).

### **Diversity in Neuroevolution**
**Quality-Diversity (QD)** methods (Lehman & Stanley, 2011; Mouret & Doncieux, 2009) maximize behavioral diversity to discover novel solutions. While QD focuses on *solution diversity*, this work targets **skill diversity** to:
- Improve sample efficiency (fewer objective queries).
- Serve as a foundation for **imitation learning** and **hierarchical RL**.
- Avoid manual distance metric design via an **information-theoretic objective**.

### **Intrinsic Motivation**
Prior work (Bellemare et al., 2016; Pathak et al., 2017) uses intrinsic motivation to learn *single* policies. This work instead learns **multiple diverse policies** by maximizing MI between skills and states. Concurrent work (Achiam et al., 2017) ties skill discriminability to **variational autoencoders (VAEs)**, but this method scales better due to:
- **Off-policy RL** (Soft Actor-Critic, or SAC).
- **State-conditioned discriminators** (vs. trajectory-level in prior work).

![Figure 1: DIAYN Algorithm: Iterative updates to the discriminator (to predict skills) and policy (to maximize skill discriminability)](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-2-0.png)

## 3 Diversity Is All You Need

This work introduces an **unsupervised reinforcement learning (RL)** framework where an agent first explores its environment without task-specific rewards ("unsupervised stage") to learn reusable **skills**, which are later fine-tuned for downstream tasks ("supervised stage"). The key insight is that skills learned without prior task knowledge can generalize across multiple tasks, improving sample efficiency during supervised learning.

---

### 3.1 How It Works

**DIAYN** (*Diversity Is All You Need*) is a method for **unsupervised skill discovery** based on three core principles:
1. **Skill-state correspondence**: Skills should map to *distinct sets of states*—different skills should lead the agent to different parts of the environment.
2. **State-based discrimination**: Skills are distinguished by the *states they visit*, not the *actions they take*, since actions may not always affect the environment observably (e.g., a robot’s internal force adjustments).
3. **Maximal diversity**: Skills should explore *diverse* state spaces while remaining distinguishable. High-entropy (random) skills must avoid overlapping with other skills to stay identifiable.

#### Mathematical Formulation
DIAYN formalizes these ideas using **information theory**:
- **Mutual information** _I(S; Z)_ maximizes the dependency between *skills (Z)* and *visited states (S)*, ensuring skills control state distributions.
- **Conditional mutual information** _I(A; Z | S)_ is minimized to prevent skills from being distinguishable by *actions (A)* alone (enforcing state-based discrimination).
- **Entropy** _H[A | S]_ of the *mixture policy* (all skills combined) is maximized to encourage exploration.

The combined objective is:
_F(θ) = I(S; Z) + H[A | S] − I(A; Z | S)_
After simplification, this reduces to:
_F(θ) = H[Z] − H[Z | S] + H[A | S, Z]_
- **H[Z]**: Maximized by using a *uniform prior* over skills (fixed in practice).
- **−H[Z | S]**: Encourages skills to be *inferable from states* (low uncertainty in _p(z | s)_).
- **H[A | S, Z]**: Promotes *randomness within each skill* (max-entropy policies).

#### Practical Optimization
Since exact computation of _p(z | s)_ is intractable, DIAYN uses a **learned discriminator** _qφ(z | s)_ to approximate the posterior, yielding a **variational lower bound** _G(θ, φ)_ on the true objective. This bound is optimized via:
- **Policy updates**: Maximize entropy and state discriminability.
- **Discriminator updates**: Improve skill inference from states.

---

### 3.2 Implementation
DIAYN is implemented using **Soft Actor-Critic (SAC)**, a max-entropy RL algorithm, with the following adaptations:
- **Skill-conditioned policy**: _πθ(a | s, z)_ takes a latent skill variable _z_ (sampled from a *categorical distribution* at the start of each episode).
- **Pseudo-reward**: Replaces task rewards during unsupervised training:
  _rz(s, a) = log qφ(z | s) − log p(z)_
  - Rewards states that are *easily discriminable* for the current skill _z_.
- **Entropy regularization**: SAC’s built-in entropy term (scaled by _α = 0.1_) balances exploration and skill distinguishability.

---
### 3.3 Stability
DIAYN avoids instabilities common in **adversarial unsupervised RL** (e.g., mode collapse) by framing skill discovery as a **cooperative game** between the policy and discriminator. Key stability properties:
- **Theoretical optimum**: In gridworlds, the optimal solution *evenly partitions* the state space among skills, with each skill covering its partition uniformly.
- **Empirical robustness**: Performance is consistent across random seeds (see ![Figure 4: Downstream task performance across seeds](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-3.png), ![Figure 6: Skill visualization](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-5-1.png), ![Figure 13: Seed sensitivity analysis](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-7-2.png)).
- **Practical reliability**: Unlike adversarial methods (e.g., GAN-based RL), DIAYN does not suffer from training instability, though formal convergence guarantees remain elusive in continuous settings (as with most RL methods using function approximation).

## 4 EXPERIMENTS

This section evaluates **DIAYN** (*Diversity Is All You Need*), a method for **unsupervised skill discovery** in reinforcement learning (RL), where agents learn diverse behaviors *without external rewards*. Experiments analyze:
1. **Properties of learned skills**: Diversity, training dynamics, and comparisons to prior work.
2. **Downstream applications**: Leveraging skills for **policy initialization**, **hierarchical RL**, and **imitation learning**.

Videos and code are available [here](https://sites.google.com/view/diayn/) and [here](https://github.com/ben-eysenbach/sac/blob/master/DIAYN.md).

---

### 4.1 ANALYSIS OF LEARNED SKILLS

#### **Key Questions & Findings**
1. **What skills does DIAYN learn?**
   DIAYN discovers **diverse, task-agnostic behaviors** across environments of varying complexity:
   - **2D Navigation**: Skills spread spatially to remain distinguishable (e.g., moving in 6 distinct directions).
     ![Figure 2a: DIAYN skills in 2D navigation](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-2-0.png)
   - **Classic Control** (e.g., inverted pendulum, mountain car): Learns *multiple* distinct solutions to the same task.
   - **Locomotion** (half cheetah, hopper, ant): Emerges complex behaviors like running, flipping, hopping, and gliding *without reward functions*.
     ![Figure 3: Locomotion skills (half cheetah, hopper, ant)](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-2.png)

2. **How do skills evolve during training?**
   - Skills **increase in diversity** over time, as measured by the discriminator’s reward signal.
   - Training dynamics are robust across random seeds (see Appendix D).
     ![Figure 2c: Training dynamics (diversity over time)](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-1.png)

3. **Do skills require disjoint state visits?**
   - No. While DIAYN favors *distinguishable* skills, they may **overlap in state space** if trajectories diverge later.
     - Example: An agent in a hallway learns skills that exit into a larger room to become distinguishable.
       ![Figure 2b: Overlapping skills in a hallway environment](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-0.png)

4. **How does DIAYN differ from Variational Intrinsic Control (VIC)?**
   - **Key improvement**: DIAYN uses a *fixed prior* over skills (`p(z)`), while VIC learns it.
   - **Problem with VIC**: The "Matthew Effect" — diverse skills are sampled more frequently, starving others of training signal.
   - **Result**: DIAYN maintains **consistent skill sampling**, leading to higher diversity.
     ![Figure 4: DIAYN vs. VIC skill sampling](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-3.png)

---

### 4.2 HARNESSING LEARNED SKILLS

DIAYN’s unsupervised skills serve as **building blocks** for three RL applications:

#### 4.2.1 ACCELERATING LEARNING WITH POLICY INITIALIZATION
- **Method**: Initialize a task-specific policy with weights from the *highest-reward DIAYN skill*, then finetune.
- **Result**: **Faster convergence** compared to training from scratch across half cheetah, hopper, and ant tasks.
  ![Figure 5: Policy initialization vs. random initialization](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-5-0.png)
- **Why it works**: The pretrained critic (though trained on pseudo-rewards) generalizes well to true task rewards.

#### 4.2.2 USING SKILLS FOR HIERARCHICAL RL
- **Challenge**: Traditional hierarchical RL often collapses to trivial solutions (e.g., all skills doing the same action).
- **DIAYN’s approach**:
  1. Learn diverse, task-agnostic skills.
  2. Train a **meta-controller** to select skills for *k* steps (e.g., 10–100 steps).
- **Results**:
  - **2D Navigation**: Performance scales with the number of skills; outperforms **VIME** (a prior unsupervised RL method).
    ![Figure 6: Hierarchical RL in 2D navigation](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-5-1.png)
  - **Complex Tasks**:
    - **Cheetah Hurdle**: Learns to jump over obstacles using skill composition.
    - **Ant Navigation**: Solves sparse-reward waypoint tasks by chaining skills.
      ![Figure 7: Hierarchical RL on cheetah hurdle and ant navigation](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-6-0.png)
  - **Prior Knowledge**: Conditioning the discriminator on task-relevant features (e.g., center of mass) improves performance further ("DIAYN+prior").

#### 4.2.3 IMITATING AN EXPERT
- **Method**:
  1. Given an expert trajectory (states only), infer the most likely DIAYN skill (`ẑ`) that generated it via:
     ```
     ẑ = argmax_z Π qφ(z|s_t) for s_t ∈ τ[expert]
     ```
  2. Use the selected skill as a policy for imitation.
- **Results**:
  - Successfully imitates **3/4** expert behaviors in half cheetah (e.g., running, limping) but struggles with complex moves like handstands.
    ![Figure 9: Imitation learning results](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-7-2.png)
  - Quantitative evaluations on classic control tasks are in Appendix G.

## 5 CONCLUSION

This paper introduces **DIAYN (Diversity is All You Need)**, a framework for **unsupervised skill discovery** that learns diverse behaviors *without external reward functions*. Key contributions include:

- **Diverse skill acquisition**: DIAYN autonomously learns a repertoire of distinct skills (e.g., locomotion gaits, manipulation strategies) for complex tasks. In many cases, these skills *incidentally solve benchmark tasks* despite never receiving task-specific rewards.
- **Versatile applications**: The learned skills enable:
  - **Fast adaptation**: Rapid fine-tuning to new tasks by leveraging pre-learned behaviors.
  - **Hierarchical RL**: Solving complex tasks by composing high-level policies over low-level skills.
  - **Imitation learning**: Replicating expert behaviors by selecting from the skill set.
- **Practical advantages**: DIAYN simplifies task learning by replacing raw action spaces with a **discrete set of reusable skills**, analogous to a "behavioral vocabulary."

### Future Directions
The authors propose several extensions:
- **Hybrid objectives**: Combining DIAYN with methods for **observation augmentation** or **reward shaping** via a unified information-theoretic framework.
- **Human-in-the-loop learning**: Improving preference-based learning by having humans *select among pre-learned skills* rather than raw actions.
- **Creative applications**: Potential use in **game design** (intuitive robot control) and **animation** (procedural character movement).

DIAYN’s unsupervised approach bridges the gap between open-ended exploration and practical task-solving, offering a scalable alternative to hand-designed reward functions.

## REFERENCES


Joshua Achiam, Harrison Edwards, Dario Amodei, and Pieter Abbeel. Variational autoencoding learning of
options by reinforcement. _NIPS Deep Reinforcement Learning Symposium_, 2017.


David Barber Felix Agakov. The im algorithm: a variational approach to information maximization. _Advances_
_in Neural Information Processing Systems_, 16:201, 2004.


Pierre-Luc Bacon, Jean Harb, and Doina Precup. The option-critic architecture. In _AAAI_, pp. 1726–1734, 2017.


Adrien Baranes and Pierre-Yves Oudeyer. Active learning of inverse models with intrinsically motivated goal
exploration in robots. _Robotics and Autonomous Systems_, 61(1):49–73, 2013.


Marc Bellemare, Sriram Srinivasan, Georg Ostrovski, Tom Schaul, David Saxton, and Remi Munos. Unifying
count-based exploration and intrinsic motivation. In _Advances in Neural Information Processing Systems_, pp.
1471–1479, 2016.


Christopher M Bishop. _Pattern Recognition and Machine Learning_ . Springer-Verlag New York, 2016.


Greg Brockman, Vicki Cheung, Ludwig Pettersson, Jonas Schneider, John Schulman, Jie Tang, and Wojciech
Zaremba. Openai gym. _arXiv preprint arXiv:1606.01540_, 2016.


Paul F Christiano, Jan Leike, Tom Brown, Miljan Martic, Shane Legg, and Dario Amodei. Deep reinforcement
learning from human preferences. In _Advances in Neural Information Processing Systems_, pp. 4302–4310,
2017.


Peter Dayan and Geoffrey E Hinton. Feudal reinforcement learning. In _Advances_ _in_ _neural_ _information_
_processing systems_, pp. 271–278, 1993.


Yan Duan, Xi Chen, Rein Houthooft, John Schulman, and Pieter Abbeel. Benchmarking deep reinforcement
learning for continuous control. In _International Conference on Machine Learning_, pp. 1329–1338, 2016.


Carlos Florensa, Yan Duan, and Pieter Abbeel. Stochastic neural networks for hierarchical reinforcement
learning. _arXiv preprint arXiv:1704.03012_, 2017.


Kevin Frans, Jonathan Ho, Xi Chen, Pieter Abbeel, and John Schulman. Meta learning shared hierarchies. _arXiv_
_preprint arXiv:1710.09767_, 2017.


Justin Fu, John Co-Reyes, and Sergey Levine. Ex2: Exploration with exemplar models for deep reinforcement
learning. In _Advances in Neural Information Processing Systems_, pp. 2574–2584, 2017.


Karol Gregor, Danilo Jimenez Rezende, and Daan Wierstra. Variational intrinsic control. _arXiv_ _preprint_
_arXiv:1611.07507_, 2016.


Shixiang Gu, Ethan Holly, Timothy Lillicrap, and Sergey Levine. Deep reinforcement learning for robotic
manipulation with asynchronous off-policy updates. In _Robotics_ _and_ _Automation_ _(ICRA),_ _2017_ _IEEE_
_International Conference on_, pp. 3389–3396. IEEE, 2017.


Tuomas Haarnoja, Haoran Tang, Pieter Abbeel, and Sergey Levine. Reinforcement learning with deep energybased policies. _arXiv preprint arXiv:1702.08165_, 2017.


Tuomas Haarnoja, Aurick Zhou, Pieter Abbeel, and Sergey Levine. Soft actor-critic: Off-policy maximum
entropy deep reinforcement learning with a stochastic actor. _arXiv preprint arXiv:1801.01290_, 2018.


9


Dylan Hadfield-Menell, Smitha Milli, Pieter Abbeel, Stuart J Russell, and Anca Dragan. Inverse reward design.
In _Advances in Neural Information Processing Systems_, pp. 6768–6777, 2017.


Karol Hausman, Jost Tobias Springenberg, Ziyu Wang, Nicolas Heess, and Martin Riedmiller. Learning an
embedding space for transferable robot skills. _International Conference on Learning Representations_, 2018.
[URL https://openreview.net/forum?id=rk07ZXZRb.](https://openreview.net/forum?id=rk07ZXZRb)


Nicolas Heess, Greg Wayne, Yuval Tassa, Timothy Lillicrap, Martin Riedmiller, and David Silver. Learning and
transfer of modulated locomotor controllers. _arXiv preprint arXiv:1610.05182_, 2016.


Peter Henderson, Riashat Islam, Philip Bachman, Joelle Pineau, Doina Precup, and David Meger. Deep
reinforcement learning that matters. _arXiv preprint arXiv:1709.06560_, 2017.


Rein Houthooft, Xi Chen, Yan Duan, John Schulman, Filip De Turck, and Pieter Abbeel. Vime: Variational
information maximizing exploration. In _Advances in Neural Information Processing Systems_, pp. 1109–1117,
2016.


Tobias Jung, Daniel Polani, and Peter Stone. Empowerment for continuous agent—environment systems.
_Adaptive Behavior_, 19(1):16–39, 2011.


Sanjay Krishnan, Roy Fox, Ion Stoica, and Ken Goldberg. Ddco: Discovery of deep continuous options for
robot learning from demonstrations. In _Conference on Robot Learning_, pp. 418–437, 2017.


Joel Lehman and Kenneth O Stanley. Abandoning objectives: Evolution through the search for novelty alone.
_Evolutionary computation_, 19(2):189–223, 2011a.


Joel Lehman and Kenneth O Stanley. Evolving a diversity of virtual creatures through novelty search and local
competition. In _Proceedings of the 13th annual conference on Genetic and evolutionary computation_, pp.
211–218. ACM, 2011b.


Robert K Merton. The matthew effect in science: The reward and communication systems of science are
considered. _Science_, 159(3810):56–63, 1968.


Piotr Mirowski, Razvan Pascanu, Fabio Viola, Hubert Soyer, Andrew J Ballard, Andrea Banino, Misha Denil,
Ross Goroshin, Laurent Sifre, Koray Kavukcuoglu, et al. Learning to navigate in complex environments.
_arXiv preprint arXiv:1611.03673_, 2016.


Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Alex Graves, Ioannis Antonoglou, Daan Wierstra, and
Martin Riedmiller. Playing atari with deep reinforcement learning. _arXiv preprint arXiv:1312.5602_, 2013.


Shakir Mohamed and Danilo Jimenez Rezende. Variational information maximisation for intrinsically motivated
reinforcement learning. In _Advances in neural information processing systems_, pp. 2125–2133, 2015.


Jean-Baptiste Mouret and Stéphane Doncieux. Overcoming the bootstrap problem in evolutionary robotics using
behavioral diversity. In _Evolutionary Computation, 2009. CEC’09. IEEE Congress on_, pp. 1161–1168. IEEE,
2009.


Kevin P Murphy. _Machine Learning:_ _A Probabilistic Perspective_ . MIT Press, 2012.


Ofir Nachum, Mohammad Norouzi, Kelvin Xu, and Dale Schuurmans. Bridging the gap between value and
policy based reinforcement learning. In _Advances in Neural Information Processing Systems_, pp. 2772–2782,
2017.


Pierre-Yves Oudeyer, Frdric Kaplan, and Verena V Hafner. Intrinsic motivation systems for autonomous mental
development. _IEEE transactions on evolutionary computation_, 11(2):265–286, 2007.


Deepak Pathak, Pulkit Agrawal, Alexei A Efros, and Trevor Darrell. Curiosity-driven exploration by selfsupervised prediction. _arXiv preprint arXiv:1705.05363_, 2017.


Vitchyr Pong, Shixiang Gu, Murtaza Dalal, and Sergey Levine. Temporal difference models: Model-free deep rl
for model-based control. _arXiv preprint arXiv:1802.09081_, 2018.


Justin K Pugh, Lisa B Soros, and Kenneth O Stanley. Quality diversity: A new frontier for evolutionary
computation. _Frontiers in Robotics and AI_, 3:40, 2016.


Richard M Ryan and Edward L Deci. Intrinsic and extrinsic motivations: Classic definitions and new directions.
_Contemporary educational psychology_, 25(1):54–67, 2000.


Jürgen Schmidhuber. Formal theory of creativity, fun, and intrinsic motivation. _IEEE_ _Transactions_ _on_ _Au-_
_tonomous Mental Development_, 2(3):230–247, 2010.


10


John Schulman, Sergey Levine, Pieter Abbeel, Michael Jordan, and Philipp Moritz. Trust region policy
optimization. In _International Conference on Machine Learning_, pp. 1889–1897, 2015a.


John Schulman, Philipp Moritz, Sergey Levine, Michael Jordan, and Pieter Abbeel. High-dimensional continuous
control using generalized advantage estimation. _arXiv preprint arXiv:1506.02438_, 2015b.


John Schulman, Pieter Abbeel, and Xi Chen. Equivalence between policy gradients and soft q-learning. _arXiv_
_preprint arXiv:1704.06440_, 2017.


Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff
Dean. Outrageously large neural networks: The sparsely-gated mixture-of-experts layer. _arXiv_ _preprint_
_arXiv:1701.06538_, 2017.


David Silver, Aja Huang, Chris J Maddison, Arthur Guez, Laurent Sifre, George Van Den Driessche, Julian
Schrittwieser, Ioannis Antonoglou, Veda Panneershelvam, Marc Lanctot, et al. Mastering the game of go with
deep neural networks and tree search. _nature_, 529(7587):484–489, 2016.


Kenneth O Stanley and Risto Miikkulainen. Evolving neural networks through augmenting topologies. _Evolu-_
_tionary computation_, 10(2):99–127, 2002.


Felipe Petroski Such, Vashisht Madhavan, Edoardo Conti, Joel Lehman, Kenneth O Stanley, and Jeff Clune.
Deep neuroevolution: Genetic algorithms are a competitive alternative for training deep neural networks for
reinforcement learning. _arXiv preprint arXiv:1712.06567_, 2017.


Sainbayar Sukhbaatar, Zeming Lin, Ilya Kostrikov, Gabriel Synnaeve, Arthur Szlam, and Rob Fergus. Intrinsic
motivation and automatic curricula via asymmetric self-play. _arXiv preprint arXiv:1703.05407_, 2017.


Brian G Woolley and Kenneth O Stanley. On the deleterious effects of a priori objectives on evolution and
representation. In _Proceedings of the 13th annual conference on Genetic and evolutionary computation_, pp.
957–964. ACM, 2011.


Yuke Zhu, Roozbeh Mottaghi, Eric Kolve, Joseph J Lim, Abhinav Gupta, Li Fei-Fei, and Ali Farhadi. Targetdriven visual navigation in indoor scenes using deep reinforcement learning. In _Robotics and Automation_
_(ICRA), 2017 IEEE International Conference on_, pp. 3357–3364. IEEE, 2017.


Brian D Ziebart, Andrew L Maas, J Andrew Bagnell, and Anind K Dey. Maximum entropy inverse reinforcement
learning. In _AAAI_, volume 8, pp. 1433–1438. Chicago, IL, USA, 2008.


11


A PSEUDO-REWARD


The log _p_ ( _z_ ) term in Equation 3 is a baseline that does not depend on the policy parameters _θ_, so
one might be tempted to remove it from the objective. We provide a two justifications for keeping
it. First, assume that episodes never terminate, but all skills eventually converge to some absorbing
state (e.g., with all sensors broken). At this state, the discriminator cannot distinguish the skills,
so its estimate is log _q_ ( _z_ _|_ _s_ ) = log(1 _/N_ ), where _N_ is the number of skills. For practical reasons,
we want to restart the episode after the agent reaches the absorbing state. Subtracting log( _z_ ) from
the pseudo-reward at every time step in our finite length episodes is equivalent to pretending that
episodes never terminate and the agent gets reward log( _z_ ) after our “artificial” termination. Second,
assuming our discriminator _qφ_ is better than chance, we see that _qφ_ ( _z_ _| s_ ) _≥_ _p_ ( _z_ ). Thus, subtracting
the log _p_ ( _z_ ) baseline ensures our reward function is always non-negative, encouraging the agent to
stay alive. Without this baseline, an optimal agent would end the episode as soon as possible. [5]


B OPTIMUM FOR GRIDWORLDS


For simple environments, we can compute an analytic solution to the DIAYN objective. For example,
consider a _N_ _× N_ gridworld, where actions are to move up/down/left/right. Any action can be taken
in any state, but the agent will stay in place if it attempts to move out of the gridworld. We use ( _x, y_ )
to refer to states, where _x, y_ _∈{_ 1 _,_ 2 _, · · ·_ _, N_ _}_ .


For simplicity, we assume that, for every skill, the distribution of states visited exactly equals that
skill’s stationary distribution over states. To clarify, we will use _πz_ to refer to the policy for skill _z_ .
We use _ρπz_ to indicate skill _z_ ’s stationary distribution over states, and _ρ_ ˆ _πz_ as the empirical distribution
over states within a single episode. Our assumption is equivalent to saying

_ρπz_ ( _s_ ) = _ρ_ ˆ _πz_ ( _s_ ) _∀s ∈S_


One way to ensure this is to assume infinite-length episodes.


We want to show that a set of skills that evenly partitions the state space is the optimum of the DIAYN
objective for this task. While we will show this only for the 2-skill case, the 4 skill case is analogous.


|Col1|Col2|Col3|Col4|Col5|Col6|
|---|---|---|---|---|---|
|||SKI|LL|||
|||||||
|||||||
|||SKI|LL|2||
|||||||



(a) Optimum Skills for Gridworld with 2 Skills



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-11-0.png)

(b) Policy for one of the optimal skills. The agent stays
in place when it attempts to leave the gridworld.



Figure 10: **Optimum for Gridworlds:** For gridworld environments, we can compute an analytic
solution to the DIAYN objective.


The optimum policies for a set of two skills are those which evenly partition the state space. We will
show that a top/bottom partition is one such (global) optima. The left/right case is analogous.

**Lemma B.1.** _A pair of skills with state distributions given below (and shown in Figure 10) are an_
_optimum for the DIAYN objective with no entropy regularization (α_ = 0 _)._


2 2
_ρπ_ 1( _x, y_ ) = _N_ [2] _[δ]_ [(] _[y]_ _[≤]_ _[N/]_ [2)] _and_ _ρπ_ 2( _x, y_ ) = _N_ [2] _[δ]_ [(] _[y]_ _[> N/]_ [2)] (4)


5In some environments, such as mountain car, it is desirable for the agent to end the episode as quickly as
possible. For these types of environments, the log _p_ ( _z_ ) baseline can be removed.


12


Before proving Lemma B.1, we note that there exist policies that achieve these stationary distributions.
Figure 10b shows one such policy, were each arrow indicates a transition with probability [1] 4 [.] [Note]

that when the agent is in the bottom row of yellow states, it does not transition to the green states,
and instead stays in place with probability [1] 4 [.] [Note that the distribution in Equation 4 satisfies the]

detailed balance equations (Murphy, 2012).


_Proof._ Recall that the DIAYN objective with no entropy regularization is:


_−H_ [ _Z_ _| S_ ] + _H_ [ _Z_ ]


Because the skills partition the states, we can always infer the skill from the state, so _H_ [ _Z_ _| S_ ] = 0.
By construction, the prior distribution over _H_ [ _Z_ ] is uniform, so _H_ [ _Z_ ] = log(2) is maximized. Thus,
a set of two skills that partition the state space maximizes the un-regularized DIAYN objective.


Next, we consider the regularized objective. In this case, we will show that while an even partition
is not perfectly optimal, it is “close” to optimal, and its “distance” from optimal goes to zero as the
gridworld grows in size. This analysis will give us additional insight into the skills preferred by the
DIAYN objective.

**Lemma B.2.** _A pair of skills with state distributions given given in Equation 4 achieve an DIAYN_
_objective within a factor of O_ (1 _/N_ ) _of the optimum, where N_ _is the gridworld size._


_Proof._ Recall that the DIAYN objective with no entropy regularization is:


_H_ [ _A | S, Z_ ] _−H_ [ _Z_ _| S_ ] + _H_ [ _Z_ ]


We have already computed the second two terms in the previous proof: _H_ [ _Z_ _|_ _S_ ] = 0 and
_H_ [ _Z_ ] = log(2). For computing the first term, it is helpful to define the set of “border states” for
a particular skill as those that do not neighbor another skill. For the skill 1 in Figure 10 (colored
yellow), the border states are: _{_ ( _x, y_ ) _| y_ = 4 _}_ . Now, computing the first term is straightforward:



3 4 [log(4)]


(b)



2
_H_ [ _A | S, Z_ ] =
_N_ [2]




( _N/_ 2 _−_ 1) _N_ log(4) + _N_
�non-border states��   - border states����




- 1 2 _[N]_ [ 2] _[ −]_ [1] 4 _[N]_



= [2 log(4)]

_N_ [2]



= [2 log(4)]




[1] 
4 _[N]_



= log(4)(1 _−_ [1]

2 _N_ [)]



Thus, the overall objective is within [log(4)] 2 _N_ of optimum.



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-12-3.png)



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-12-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-12-2.png)

Figure 11: The DIAYN objective prefers skills that _(Left)_ partition states into sets with short borders
and _(Right)_ which correspond to bottleneck states.


Note that the term for maximum entropy over actions ( _H_ [ _A_ _|_ _S, Z_ ]) comes into conflict with the
term for discriminability ( _−H_ [ _Z_ _| S_ ]) at states along the border between two skills. Everything else
being equal, this conflict encourages DIAYN to produce skills that have small borders, as shown in
Figure 11. For example, in a gridworld with dimensions _N_ _< M_, a pair of skills that split along the
first dimension (producing partitions of size ( _N, M/_ 2)) would achieve a larger (better) objective than
skills that split along the second dimension. This same intuition that DIAYN seeks to minimize the
border length between skills results in DIAYN preferring partitions that correspond to bottleneck
states (see Figure 11b).


13


C EXPERIMENTAL DETAILS


In our experiments, we use the same hyperparameters as those in Haarnoja et al. (2018), with one
notable exception. For the Q function, value function, and policy, we use neural networks with 300
hidden units instead of 128 units. We found that increasing the model capacity was necessary to
learn many diverse skills. When comparing the “skill initialization” to the “random initialization” in
Section 4.2, we use the same model architecture for both methods. To pass skill _z_ to the Q function,
value function, and policy, we simply concatenate _z_ to the current state _st_ . As in Haarnoja et al.
(2018), epochs are 1000 episodes long. For all environments, episodes are at most 1000 steps long,
but may be shorter. For example, the standard benchmark hopper environment terminates the episode
once it falls over. Figures 2 and 5 show up to 1000 epochs, which corresponds to at most 1 million
steps. We found that learning was most stable when we scaled the maximum entropy objective
( _H_ [ _A | S, Z_ ] in Eq. 1) by _α_ = 0 _._ 1. We use this scaling for all experiments.


C.1 ENVIRONMENTS


Most of our experiments used the following, standard RL environments (Brockman et al., 2016):
HalfCheetah-v1, Ant-v1, Hopper-v1, MountainCarContinuous-v0, and InvertedPendulum-v1. The
simple 2D navigation task used in Figures 2a and 6 was constructed as follows. The agent starts in
the center of the unit box. Observations _s ∈_ [0 _,_ 1] [2] are the agent’s position. Actions _a ∈_ [ _−_ 0 _._ 1 _,_ 0 _._ 1] [2]
directly change the agent’s position. If the agent takes an action to leave the box, it is projected to the
closest point inside the box.


The cheetah hurdle environment is a modification of HalfCheetah-v1, where we added boxes with
shape _H_ = 0 _._ 25 _m, W_ = 0 _._ 1 _m, D_ = 1 _._ 0 _m_, where the width dimension is along the same axis as the
cheetah’s forward movement. We placed the boxes ever 3 meters, start at _x_ = _−_ 1 _m_ .


The ant navigation environment is a modification of Ant-v1. To improve stability, we follow Pong
et al. (2018) and lower the gear ratio of all joints to 30. The goals are the corners of a square, centered
at the origin, with side length of 4 meters: [(2 _,_ 2) _,_ (2 _, −_ 2) _,_ ( _−_ 2 _, −_ 2) _,_ ( _−_ 2 _,_ 2) _,_ (2 _,_ 2)]. The ant starts
at the origin, and receives a reward of +1 when its center of mass is within 0.5 meters of the correct
next goal. Each reward can only be received once, so the maximum possible reward is +5.


C.2 HIERARCHICAL RL EXPERIMENT


For the 2D navigation experiment shown in Figure 6, we first learned a set of skills on the point
environment. Next, we introduced a reward function _rg_ ( _s_ ) = _−∥s −_ _g∥_ [2] 2 [penalizing the distance]
from the agent’s state to some goal, and applied the hierarchical algorithm above. In this task, the
DIAYN skills provided sufficient coverage of the state space that the hierarchical policy only needed
to take a single action (i.e., choose a single skill) to complete the task.


14


D MORE ANALYSIS OF DIAYN SKILLS


D.1 TRAINING OBJECTIVES


Figure 12: **Objectives** : We plot the two terms from our objective (Eq. 1) throughout training. While
the entropy regularizer (blue) quickly plateaus, the discriminability term (orange) term continues to
increase, indicating that our skills become increasingly diverse without collapsing to deterministic
policies. This plot shows the mean and standard deviation across 5 seeds for learning 20 skills in half
cheetah environment. Note that log2(1 _/_ 20) _≈−_ 3, setting a lower bound for log _qφ_ ( _z_ _| s_ ).


To provide further intuition into our approach, Figure 12 plots the two terms in our objective
throughout training. Our skills become increasingly diverse throughout training without converging
to deterministic policies.


Figure 13: We repeated the experiment from Figure 2 with 5 random seeds to illustrate the robustness
of our method to random seed.


To illustrate the stability of DIAYN to random seed, we repeated the experiment in Figure 2 for 5
random seeds. Figure 13 illustrates that the random seed has little effect on the training dynamics.


D.2 EFFECT OF ENTROPY REGULARIZATION


**Question 9.** _Does entropy regularization lead to more diverse skills?_



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-14-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-14-1.png)

To answer this question, we apply our method
to a 2D point mass. The agent controls the orientation and forward velocity of the point, with
is confined within a 2D box. We vary the entropy regularization _α_, with larger values of _α_
corresponding to policies with more stochastic
actions. With small _α_, we learn skills that move
large distances in different directions but fail to



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-14-2.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-14-3.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-14-4.png)

_α_ = 0 _._ 01 _α_ = 1 _α_ = 10



15


explore large parts of the state space. Increasing _α_ makes the skills visit a more diverse set of states,
which may help with exploration in complex state spaces. It is difficult to discriminate skills when _α_
is further increased.


D.3 DISTRIBUTION OVER TASK REWARD


(a) Hopper (b) Half Cheetah (c) Ant


Figure 15: **Task reward of skills learned without reward** : While our skills are learned without the
task reward function, we evaluate each with the task reward function for analysis. The wide range of
rewards shows the diversity of the learned skills. In the hopper and half cheetah tasks, many skills
achieve large task reward, despite not observing the task reward during training. As discussed in prior
work (Henderson et al., 2017; Duan et al., 2016), standard model-free algorithms trained directly on
the task reward converge to scores of 1000 - 3000 on hopper, 1000 - 5000 on cheetah, and 700 - 2000
on ant.


In Figure 15, we take the skills learned without any rewards, and evaluate each of them on the
standard benchmark reward function. We compare to random (untrained) skills. The wide distribution
over rewards is evidence that the skills learned are diverse. For hopper, some skills hop or stand
for the entire episode, receiving a reward of at least 1000. Other skills aggressively hop forwards
or dive backwards, and receive rewards between 100 and 1000. Other skills fall over immediately
and receive rewards of less than 100. The benchmark half cheetah reward includes a control penalty
for taking actions. Unlike random skills, learned skills rarely have task reward near zero, indicating
that all take actions to become distinguishable. Skills that run in place, flop on their nose, or do
backflips receive reward of -100. Skills that receive substantially smaller reward correspond to
running quickly backwards, while skills that receive substantially larger reward correspond to running
forward. Similarly, the benchmark ant task reward includes both a control penalty and a survival
bonus, so random skills that do nothing receive a task reward near 1000. While no single learned
skill learns to run directly forward and obtain a task reward greater than 1000, our learned skills run
in different patterns to become discriminable, resulting in a lower task reward.


D.4 EXPLORATION


**Question 10.** _Does DIAYN explore effectively in complex environments?_


We apply DIAYN to three standard RL benchmark environments: half-cheetah, hopper, and ant. In all
environments, we learn diverse locomotion primitives, as shown in Figure 3. Despite never receiving
any reward, the half cheetah and hopper learn skills that move forward and achieve large task reward
on the corresponding RL benchmarks, which all require them to move forward at a fast pace. Half
cheetah and hopper also learn skills that move backwards, corresponding to receiving a task reward
much smaller than what a random policy would receive. Unlike hopper and half cheetah, the ant is
free to move in the XY plane. While it learns skills that move in different directions, most skills move
in arcs rather than straight lines, meaning that we rarely learn a single skill that achieves large task
reward on the typical task of running forward. In the appendix, we visualize the objective throughout
training.


In Figure 16, we evaluate all skills on three reward functions: running (maximize X coordinate),
jumping (maximize Z coordinate) and moving (maximize L2 distance from origin). For each skill,
DIAYN learns some skills that achieve high reward. We compare to single policy trained with a
pure exploration objective (VIME (Houthooft et al., 2016)). Whereas previous work (e.g., Pathak
et al. (2017); Bellemare et al. (2016); Houthooft et al. (2016)) finds a single policy that explores well,
DIAYN optimizes a _collection_ of policies, which enables more diverse exploration.


16



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-15-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-15-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-15-2.png)
![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-16-0.png)

Figure 16: **Exploration** : We take DIAYN skills learned without a reward function, and evaluate
on three natural reward functions: running, jumping, and moving away from the origin. For all
tasks, DIAYN learns some skills that perform well. In contrast, a single policy that maximizes an
exploration bonus (VIME) performs poorly on all tasks.


E LEARNING _p_ ( _z_ )


We used our method as a starting point when comparing to VIC (Gregor et al., 2016) in Section 4.2.
While _p_ ( _z_ ) is fixed in our method, we implement VIC by learning _p_ ( _z_ ). In this section, we describe
how we learned _p_ ( _z_ ), and show the effect of learning _p_ ( _z_ ) rather than leaving it fixed.


E.1 HOW TO LEARN _p_ ( _z_ )


We choose _p_ ( _z_ ) to optimize the following objective, where _pz_ ( _s_ ) is the distribution over states
induced by skill _s_ :


_H_ [ _S, Z_ ] = _H_ [ _Z_ ] _−H_ [ _Z_ _| S_ ]



= 


_−p_ ( _z_ ) log _p_ ( _z_ ) +  
_z_ _z_



E _s∼pz_ ( _s_ ) [log _p_ ( _z_ _| s_ )]
_z_



= - _p_ ( _z_ ) �E _s∼pz_ ( _s_ ) [log _p_ ( _z_ _| s_ )] _−_ log _p_ ( _z_ )�

_z_



For clarity, we define _p_ _[t]_ _z_ [(] _[s]_ [)][ as the distribution over states induced by skill] _[ z]_ [ at epoch] _[ t]_ [, and define]
_ℓt_ ( _z_ ) as an approximation of E[log _p_ ( _z_ _| s_ )] using the policy and discriminator from epoch _t_ :


_ℓt_ ( _z_ ) ≜ E _s∼ptz_ ( _s_ )[log _qt_ ( _z_ _| s_ )]


Noting that _p_ ( _z_ ) is constrained to sum to 1, we can optimize this objective using the method of
Lagrange multipliers. The corresponding Lagrangian is







_L_ ( _p_ ) = - _p_ ( _z_ ) ( _ℓt_ ( _z_ ) _−_ log _p_ ( _z_ )) + _λ_


_z_



��



_p_ ( _z_ ) _−_ 1

_z_



whose derivative is



_∂L_ - _−_ 1
_p_ ( _z_ )
_∂p_ ( _z_ ) [=][ ��] - _p_ ( [�] _z_ )




+ _ℓt_ ( _z_ ) _−_ log _p_ ( _z_ ) + _λ_



= _ℓt_ ( _z_ ) _−_ log _p_ ( _z_ ) + _λ −_ 1


Setting the derivative equal to zero, we get


log _p_ ( _z_ ) = _ℓt_ ( _z_ ) + _λ −_ 1


and finally arrive at
_p_ ( _z_ ) _∝_ _e_ _[ℓ][t]_ [(] _[z]_ [)]


17


![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-17-0.png)

Figure 17: **Effect of learning** _p_ ( _z_ ): We plot the effective number of skills that are sampled from
the skill distribution _p_ ( _z_ ) throughout training. Note how learning _p_ ( _z_ ) greatly reduces the effective
number on inverted pendulum and mountain car. We show results from 3 random seeds for each
environment.


E.2 EFFECT OF LEARNING _p_ ( _z_ )


In this section, we briefly discuss the effect of learning _p_ ( _z_ ) rather than leaving it fixed. To study the
effect of learning _p_ ( _z_ ), we compared the entropy of _p_ ( _z_ ) throughout training. When _p_ ( _z_ ) is fixed, the
entropy is a constant (log(50) _≈_ 3 _._ 9). To convert nats to a more interpretable quantity, we compute
the effective number of skills by exponentiation the entropy:


effective num. skills ≜ _e_ _[H]_ [[] _[Z]_ []]


Figure 17 shows the effective number of skills for half cheetah, inverted pendulum, and mountain
car. Note how the effective number of skills drops by a factor of 10x when we learn _p_ ( _z_ ). This
observation supports our claim that learning _p_ ( _z_ ) results in learning fewer diverse skills.


F VISUALIZING LEARNED SKILLS


F.1 CLASSIC CONTROL TASKS


(a) Inverted Pendulum (b) Mountain Car


Figure 18: **Visualizing** **Skills** : For every skill, we collect one trajectory and plot the agent’s X
coordinate across time. For inverted pendulum (top), we only plot skills that balance the pendulum.
Note that among balancing skills, there is a wide diversity of balancing positions, control frequencies,
and control magnitudes. For mountain car (bottom), we show skills that achieve larger reward
(complete the task), skills with near-zero reward, and skills with very negative reward. Note that
skills that solve the task (green) employ varying strategies.


In this section, we visualize the skills learned for inverted pendulum and mountain car without a
reward. Not only does our approach learn skills that solve the task without rewards, it learns multiple
distinct skills for solving the task. Figure 18 shows the X position of the agent across time, within
one episode. For inverted pendulum (Fig. 18a), we plot only skills that solve the task. Horizontal
lines with different X coordinates correspond to skills balancing the pendulum at different positions
along the track. The periodic lines correspond to skills that oscillate back and forth while balancing


18



![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-17-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-17-2.png)
Figure 19: **Half cheetah skills** : We show skills learned by half-cheetah with no reward.


the pendulum. Note that skills that oscillate have different X positions, amplitudes, and periods. For
mountain car (Fig. 18b), skills that climb the mountain employ a variety of strategies for to do so.
Most start moving backwards to gather enough speed to summit the mountain, while others start
forwards, then go backwards, and then turn around to summit the mountain. Additionally, note that
skills differ in when the turn around and in their velocity (slope of the green lines).


F.2 SIMULATED ROBOT TASKS


Figures 19, 20, and 21 show more skills learned _without reward_ .


19


![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-2.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-3.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-4.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-5.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-6.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-7.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-8.png)

Figure 20: **Hopper Skills** : We show skills learned by hopper with no reward.


20


![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-0.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-1.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-2.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-3.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-4.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-5.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-6.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-7.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-8.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-9.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-10.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-11.png)

![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-20-12.png)

Figure 21: **Ant skills** : We show skills the ant learns without any supervision. Ant learns _(top row)_ to
move right, _(middle row)_ to move left, _(bottom row, left to right)_ to move up, to move down, to flip
on its back, and to rotate in place.


21


![](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-21-0.png)

Figure 22: **Imitating** **an** **expert** : Across 600 imitation tasks, we find our method more closely
matches the expert than all baselines.


G IMITATION LEARNING


Given the expert trajectory, we use our learned discriminator to estimate which skill was most likely
to have generated the trajectory:


_z_ ˆ = arg max Π _st∈τ ∗_ _qφ_ ( _z_ _| st_ )
_z_


As motivation for this optimization problem, note that each skill induces a distribution over states,
_p_ _[z]_ ≜ _p_ ( _s_ _|_ _z_ ). We use _p_ _[∗]_ to denote the distribution over states for the expert policy. With a fixed
prior distribution _p_ ( _z_ ) and a perfect discriminator _qφ_ ( _z_ _| s_ ) = _p_ ( _z_ _| s_ ), we have _p_ ( _s | z_ ) _∝_ _qφ_ ( _z_ _| s_ )
as a function of _z_ . Thus, Equation G is an M-projection of the expert distribution over states onto the
family of distributions over states, _P_ = _{p_ _[z]_ _}_ :

arg min _D_ ( _p_ _[∗]_ _|| p_ _[z]_ ) (5)
_p_ _[z]_ _∈P_


For clarity, we omit a constant that depends only on _p_ _[∗]_ . Note that the use of an M-projection,
rather than an I-projection, helps guarantee that the retrieved skill will visit all states that the expert
visits (Bishop, 2016). In our experiments, we solve Equation 5 by simply iterating over skills.


G.1 IMITATION LEARNING EXPERIMENTS


The “expert” trajectories are actually generated synthetically in these experiments, by running a
different random seed of our algorithm. A different seed is used to ensure that the trajectories are not
actually produced by any of the currently available skills. Of course, in practice, the expert trajectories
might be provided by any other means, including a human. For each expert trajectory, we retrieve
the closest DIAYN skill _z_ ˆ using Equation 4.2.3. Evaluating _qφ_ (ˆ _z_ _|_ _τ_ _[∗]_ ) gives us an estimate of the
probability that the imitation will match the expert (e.g., for a safety critical setting). This quantity is
useful for predicting how accurately our method will imitate an expert before executing the imitation
policy. In a safety critical setting, a user may avoid attempting tasks where this score is low. We
compare our method to three baselines. The “low entropy” baseline is a variant on our method with
lower entropy regularization. The “learned _p_ ( _z_ )” baseline learns the distribution over skills. Note
that Variational Intrinsic Control (Gregor et al., 2016) is a combination of the “low entropy” baseline
and the “learned _p_ ( _z_ )” baseline. Finally, the “few skills” baseline learns only 5 skills, whereas all
other methods learn 50. Figure 22 shows the results aggregated across 600 imitation tasks. The
X-axis shows the discriminator score, our estimate for how well the imitation policy will match the
expert. The Y-axis shows the true distance between the trajectories, as measured by L2 distance
in state space. For all methods, the distance between the expert and the imitation decreases as the
discriminator’s score increases, indicating that the discriminator’s score is a good predictor of task
performance. Our method consistently achieves the lowest trajectory distance among all methods.
The “low entropy” baseline is slightly worse, motivating our decision to learn maximum entropy
skills. When imitating tasks using the “few skills” baseline, the imitation trajectories are even further
from the expert trajectory. This is expected – by learning more skills, we obtain a better “coverage”
over the space of skills. A “learn _p_ ( _z_ )” baseline that learns the distribution over skills also performs
poorly. Recalling that Gregor et al. (2016) is a combination of the “low entropy” baseline and the
“learn _p_ ( _z_ )” baseline, this plot provides evidence that using maximum entropy policies and fixing the
distribution for _p_ ( _z_ ) are two factors that enabled our method to scale to more complex tasks.


22