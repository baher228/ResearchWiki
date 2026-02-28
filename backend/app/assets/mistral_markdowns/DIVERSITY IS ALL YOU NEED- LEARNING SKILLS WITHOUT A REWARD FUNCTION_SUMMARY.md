# Diversity is All You Need: Learning Skills Without a Reward Function

**Diversity is All You Need (DIAYN)** is an unsupervised reinforcement learning (RL) method that enables agents to autonomously discover diverse, useful skills without external reward signals. By maximizing an information-theoretic objective, DIAYN learns policies that explore the environment in distinct, semantically meaningful ways—such as walking, jumping, or flipping—without any task-specific guidance. The learned skills can later be repurposed for hierarchical RL, imitation learning, or fine-tuning on downstream tasks, addressing challenges like sparse rewards, exploration, and sample efficiency.

---
## Abstract

DIAYN introduces a framework for **unsupervised skill discovery** in reinforcement learning, where agents learn a repertoire of behaviors without external rewards. The core idea is to maximize **mutual information** between a latent skill variable *z* and the states *s* visited by the agent, while encouraging **maximum entropy** in the action space to ensure diversity. This objective leads to the emergence of distinct, interpretable skills (e.g., running, hopping, or flipping) in simulated robotic tasks.

Key contributions:
- A **theoretically grounded** objective for unsupervised skill learning, combining mutual information and entropy maximization.
- Empirical validation on **simulated robotic tasks** (e.g., HalfCheetah, Ant, Hopper), where DIAYN discovers skills that solve benchmark tasks despite never receiving task rewards.
- Demonstrations of how pretrained skills can:
  - **Accelerate learning** on downstream tasks via policy initialization.
  - **Enable hierarchical RL** by composing skills to solve complex, sparse-reward problems.
  - **Facilitate imitation learning** by matching expert trajectories to learned skills.
- Stability and scalability improvements over prior work (e.g., VIME, VIC) through fixed priors and maximum entropy policies.

---
## Introduction

### Motivation
Traditional RL relies on **handcrafted reward functions** to guide agents toward desired behaviors. However, designing rewards is often:
- **Labor-intensive**: Requires domain expertise (e.g., tuning weights for robotic locomotion).
- **Brittle**: Poorly specified rewards can lead to unintended behaviors (e.g., reward hacking).
- **Limiting**: Agents may fail to explore useful behaviors not directly incentivized by the reward.

**Unsupervised skill discovery** addresses these challenges by learning a diverse set of behaviors *without* external rewards. These skills can later be repurposed for:
- **Hierarchical RL**: Decomposing complex tasks into reusable primitives.
- **Exploration**: Overcoming sparse rewards by leveraging pretrained skills.
- **Imitation learning**: Matching expert demonstrations to learned skills.
- **Sample efficiency**: Reducing the need for task-specific data collection.

### Key Insights
1. **Discriminability**: Skills should be distinguishable by the states they visit (not just actions).
2. **Diversity**: Skills should explore distinct regions of the state space to maximize coverage.
3. **Entropy**: Policies should remain stochastic to avoid collapsing into deterministic, narrow behaviors.

DIAYN operationalizes these insights via an **information-theoretic objective** that balances:
- **Mutual information** *I(S; Z)*: Ensures skills are identifiable from states.
- **Entropy regularization** *H[A|S, Z]*: Encourages exploration within each skill.

---
## Related Work

### Hierarchical RL
Prior methods (e.g., [Option-Critic](https://arxiv.org/abs/1609.05140), [FeUdal Networks](https://papers.nips.cc/paper/1993-feudal-reinforcement-learning)) learn skills to maximize a *known* reward function, often suffering from:
- **Meta-policy collapse**: The high-level controller ignores suboptimal skills, starving them of gradients.
- **Task specificity**: Skills are tailored to a single reward, limiting transferability.

DIAYN avoids these issues by:
- Using a **random meta-policy** during unsupervised training (all skills receive equal attention).
- Learning **task-agnostic** skills that generalize across tasks.

### Information-Theoretic RL
DIAYN builds on connections between RL and information theory (e.g., [Maximum Entropy RL](https://arxiv.org/abs/1704.06440), [Empowerment](https://arxiv.org/abs/1509.08731)):
- **Empowerment** maximizes *I(A; S)*: Agents seek states where actions have high influence.
- **DIAYN** maximizes *I(S; Z)*: A *hierarchical* agent’s skills (not just actions) should control state visitation.

Key differences from prior work (e.g., [VIC](https://arxiv.org/abs/1611.07507), [Gregor et al. 2016](https://arxiv.org/abs/1611.07507)):
| Method       | Learns *p(z)* | Entropy Regularization | Discriminator Input       | Scalability          |
|--------------|---------------|------------------------|---------------------------|----------------------|
| VIC          | Yes           | No                     | Final state               | Limited (gridworlds)  |
| DIAYN        | **No (fixed)** | **Yes (max entropy)**  | **All states in trajectory** | Scales to MuJoCo tasks |

### Diversity-Driven Evolution
Methods like [Novelty Search](https://dl.acm.org/doi/10.1145/2001576.2001695) maximize behavioral diversity in evolutionary algorithms. DIAYN differs by:
- Using **gradient-based RL** (scalable to high-dimensional tasks).
- Formulating diversity as **mutual information**, avoiding manual distance metrics.

---
## Method

### Objective
DIAYN optimizes the following objective for a set of skills parameterized by *z*:
\[
F(\theta) = \underbrace{I(S; Z)}_{\text{Skill discriminability}} + \underbrace{H[A|S]}_{\text{Mixture entropy}} - \underbrace{I(A; Z|S)}_{\text{Action-skill dependence}}
\]
Simplified, this reduces to:
\[
F(\theta) = H[Z] - H[Z|S] + H[A|S, Z]
\]
- **H[Z]**: Maximized by fixing *p(z)* to a uniform prior.
- **−H[Z|S]**: Encourages skills to visit distinct states (easy to infer *z* from *s*).
- **H[A|S, Z]**: Maximizes entropy of each skill’s policy (exploration).

### Practical Implementation
1. **Skill-conditioned policy**: *πθ(a|s, z)* is trained via [Soft Actor-Critic (SAC)](https://arxiv.org/abs/1801.01290), which inherently maximizes entropy.
2. **Discriminator**: A classifier *qφ(z|s)* predicts the skill *z* from states *s*.
3. **Pseudo-reward**: The policy is trained to maximize:
   \[
   r_z(s, a) = \log q_\phi(z|s) - \log p(z)
   \]
   - Rewards states where *z* is easily identifiable.
   - Subtracts *log p(z)* to ensure non-negativity (encourages long trajectories).

**Algorithm 1**: DIAYN Training Loop
![Figure 1: DIAYN Algorithm](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-2-0.png)
*Caption*: Alternate between:
1. Updating the discriminator *qφ* to better predict *z* from *s*.
2. Updating the policy *πθ* to visit states that maximize *rz(s, a)*.

### Stability
- **Cooperative game**: Unlike adversarial methods (e.g., GANs), DIAYN’s policy and discriminator collaborate, improving stability.
- **Theoretical optimum**: In gridworlds, the global optimum partitions the state space evenly among skills (proof in Appendix B).
- **Empirical robustness**: Performance is consistent across random seeds (Figure 13).

---
## Experiments & Results

### Analysis of Learned Skills
#### **Question 1: What skills does DIAYN learn?**
DIAYN discovers interpretable, diverse skills across tasks:
- **2D Navigation**: Skills move to distinct regions of the space.
  ![Figure 2a: 2D Navigation Skills](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-1.png)
  *Caption*: 6 skills partition the 2D box into distinct regions.

- **Classic Control**:
  - **Inverted Pendulum**: Learns to balance at different positions/angles.
  - **Mountain Car**: Discovers multiple strategies to climb the hill (e.g., varying turn-around points).
  ![Figure 18: Classic Control Skills](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-19-0.png)
  *Caption*: Skills for inverted pendulum (top) and mountain car (bottom) show diverse solutions.

- **Simulated Robotics**:
  - **HalfCheetah**: Runs forward/backward, flips, or falls.
  - **Hopper**: Hops forward/backward, balances, or dives.
  - **Ant**: Walks in arcs, spins, or flips.
  ![Figure 3: Locomotion Skills](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-2.png)
  *Caption*: Emergent skills for HalfCheetah, Hopper, and Ant.

#### **Question 2: How do skills evolve during training?**
Skills become increasingly diverse over time, as measured by the discriminator’s confidence (*log qφ(z|s)*).
![Figure 2c: Training Dynamics](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-4-3.png)
*Caption*: Diversity (orange) increases throughout training, while entropy (blue) plateaus.

#### **Question 3: Can skills overlap?**
Yes. Skills may share states early in a trajectory if they later diverge (e.g., exiting a hallway to reach distinct rooms).
![Figure 2b: Overlapping Skills](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-5-0.png)
*Caption*: Skills overlap in the hallway but separate in the room.

#### **Question 4: Why fix *p(z)* instead of learning it?**
Learning *p(z)* (as in VIC) leads to a "Matthew Effect": diverse skills are sampled more frequently, starving others of gradients. DIAYN’s fixed uniform prior ensures all skills are explored.
![Figure 4: Fixed vs. Learned *p(z)*](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-5-1.png)
*Caption*: VIC collapses to ~5 effective skills, while DIAYN maintains diversity.

### Harnessing Learned Skills
#### **1. Policy Initialization**
Pretrained DIAYN skills accelerate learning on downstream tasks by providing a strong initialization.
- **Setup**: Fine-tune the highest-reward skill on benchmark tasks (HalfCheetah, Hopper, Ant).
- **Result**: DIAYN-initialized policies learn **2–5× faster** than random initialization.
  ![Figure 5: Policy Initialization](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-6-0.png)
  *Caption*: Fine-tuning DIAYN skills (orange) outperforms training from scratch (blue).

#### **2. Hierarchical RL**
DIAYN skills serve as primitives for a meta-controller, enabling solving complex sparse-reward tasks.
- **Tasks**:
  - **Cheetah Hurdle**: Jump over obstacles.
  - **Ant Navigation**: Visit waypoints in sequence (sparse rewards).
- **Baselines**: TRPO, SAC, VIME (exploration bonus).
- **Result**: DIAYN hierarchies outperform all baselines.
  ![Figure 7: Hierarchical RL](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-6-1.png)
  *Caption*: DIAYN + hierarchy solves hurdle jumping (left) and navigation (right).

#### **3. Imitation Learning**
Given an expert trajectory *τ***, DIAYN retrieves the closest skill via:
\[
\hat{z} = \arg\max_z \prod_{s_t \in \tau^*} q_\phi(z|s_t)
\]
- **Evaluation**: Matches expert trajectories in HalfCheetah (e.g., running, flipping).
  ![Figure 9: Imitation Examples](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-7-3.png)
  *Caption*: DIAYN imitates 3/4 expert behaviors (fails on handstand).

- **Quantitative Results**: Outperforms baselines (low entropy, learned *p(z)*, few skills) across 600 tasks.
  ![Figure 22: Imitation Performance](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DIVERSITY IS ALL YOU NEED- LEARNING SKILLS WITHOUT A REWARD FUNCTION_images/DIVERSITY-IS-ALL-YOU-NEED--LEARNING-SKILLS-WITHOUT-A-REWARD-FUNCTION.pdf-21-0.png)
  *Caption*: DIAYN achieves lower trajectory error (y-axis) for a given discriminator score (x-axis).

---
## Conclusion

### Summary of Contributions
1. **Unsupervised Skill Discovery**: DIAYN learns diverse, interpretable skills without rewards by maximizing *I(S; Z) + H[A|S, Z]*.
2. **Empirical Validation**: Skills emerge in complex tasks (e.g., HalfCheetah backflips) and solve benchmark tasks despite no task rewards.
3. **Downstream Applications**:
   - **Policy initialization**: 2–5× faster learning.
   - **Hierarchical RL**: Solves sparse-reward tasks (e.g., Ant navigation).
   - **Imitation learning**: Matches expert trajectories.
4. **Stability**: Fixed *p(z)* and max-entropy policies avoid collapse seen in prior work (e.g., VIC).

### Broader Impact
- **Exploration**: Pretrained skills reduce the burden of reward engineering.
- **Hierarchy**: Skills act as reusable primitives for complex tasks.
- **Generalization**: Task-agnostic skills transfer across problems.
- **Human-in-the-loop**: Skills could be selected by human feedback for preference learning.

### Future Directions
- **Scaling to real robots**: Test on physical systems (e.g., legged robots).
- **Combining with reward learning**: Use DIAYN for exploration + learned rewards for task solving.
- **Multi-agent skills**: Extend to collaborative or competitive settings.
- **Curriculum learning**: Automatically increase skill complexity over time.

---
## References

- Achiam, J., Edwards, H., Amodei, D., & Abbeel, P. (2017). *Variational Autoencoding Learning of Options by Reinforcement*. NIPS Deep RL Symposium.
- Bacon, P. L., Harb, J., & Precup, D. (2017). *The Option-Critic Architecture*. AAAI.
- Bellemare, M. G., Srinivasan, S., Ostrovski, G., Schaul, T., Saxton, D., & Munos, R. (2016). *Unifying Count-Based Exploration and Intrinsic Motivation*. NeurIPS.
- Brockman, G., Cheung, V., Pettersson, L., et al. (2016). *OpenAI Gym*. arXiv:1606.01540.
- Florensa, C., Duan, Y., & Abbeel, P. (2017). *Stochastic Neural Networks for Hierarchical Reinforcement Learning*. arXiv:1704.03012.
- Gregor, K., Rezende, D. J., & Wierstra, D. (2016). *Variational Intrinsic Control*. arXiv:1611.07507.
- Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018). *Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL*. arXiv:1801.01290.
- Houthooft, R., Chen, X., Duan, Y., Schulman, J., De Turck, F., & Abbeel, P. (2016). *VIME: Variational Information Maximizing Exploration*. NeurIPS.
- Lehman, J., & Stanley, K. O. (2011). *Abandoning Objectives: Evolution Through the Search for Novelty Alone*. Evolutionary Computation.
- Levine, S., & Abbeel, P. (2014). *Learning Complex Neural Network Policies with Trajectory Optimization*. ICML.
- Mnih, V., Kavukcuoglu, K., Silver, D., et al. (2013). *Playing Atari with Deep Reinforcement Learning*. arXiv:1312.5602.
- Pathak, D., Agrawal, P., Efros, A. A., & Darrell, T. (2017). *Curiosity-Driven Exploration by Self-Supervised Prediction*. arXiv:1705.05363.
- Schulman, J., Levine, S., Abbeel, P., Jordan, M., & Moritz, P. (2015). *Trust Region Policy Optimization*. ICML.
- Silver, D., Huang, A., Maddison, C. J., et al. (2016). *Mastering the Game of Go with Deep Neural Networks and Tree Search*. Nature.
- Stanley, K. O., & Miikkulainen, R. (2002). *Evolving Neural Networks Through Augmenting Topologies*. Evolutionary Computation.