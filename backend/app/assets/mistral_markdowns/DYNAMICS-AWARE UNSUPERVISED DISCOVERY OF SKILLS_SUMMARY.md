# Dynamics-Aware Unsupervised Discovery of Skills (DADS)

**Archit Sharma**, Shixiang Gu, Sergey Levine, Vikash Kumar, Karol Hausman
*Google Brain*
Published at **ICLR 2020**
[Open-source implementation](https://github.com/google-research/dads) | [Project page](https://sites.google.com/view/dads-skill)

---

## Abstract

**Dynamics-Aware Discovery of Skills (DADS)** is an unsupervised reinforcement learning (RL) algorithm that simultaneously discovers **predictable behaviors** (skills) and learns their **dynamics models** without extrinsic rewards. Unlike traditional **model-based RL (MBRL)**, which struggles to learn accurate global dynamics models for complex systems, DADS focuses on learning **local skill-conditioned dynamics** that are easier to model and generalize. The discovered skills are optimized for **predictability** and **diversity**, enabling **zero-shot planning** in downstream tasks via **model-predictive control (MPC)**.

Key contributions:
- Unsupervised discovery of **continuous, low-variance skills** in high-dimensional state spaces.
- Joint learning of **skill-conditioned dynamics models** for model-based planning.
- **Zero-shot generalization** to downstream tasks via hierarchical composition of skills.
- Outperforms standard MBRL, model-free goal-conditioned RL, and prior hierarchical RL methods.

---

## Introduction

### Motivation
Deep RL excels at solving complex tasks but often struggles with **generalization** to new scenarios. **Model-based RL (MBRL)** addresses this by learning dynamics models for planning, but scaling to high-dimensional, discontinuous systems remains challenging. **DADS** bridges this gap by:
1. **Discovering skills** (temporally extended actions) that are **diverse yet predictable**.
2. **Learning skill-conditioned dynamics models** to enable planning in the **latent space of skills**.
3. **Composing skills hierarchically** for zero-shot adaptation to downstream tasks.

### Key Insight
Instead of learning a **single global dynamics model** (which is hard to scale), DADS learns **multiple local models**, each conditioned on a skill. This modularity improves tractability and generalization.

---
## Related Work

### Unsupervised Skill Discovery
Prior work uses **mutual information (MI) maximization** to discover diverse skills by encouraging state-space coverage (Eysenbach et al., 2018; Gregor et al., 2016). However, these methods:
- Optimize **only for diversity**, leading to high-variance, unstable skills.
- Lack **predictability**, limiting utility for hierarchical composition.

DADS extends this by optimizing for **both diversity and predictability**, making skills more amenable to planning.

### Model-Based RL (MBRL)
MBRL methods (Chua et al., 2018; Nagabandi et al., 2018) learn global dynamics models but face challenges:
- **Scalability**: High-dimensional state spaces require complex models (e.g., Bayesian neural networks).
- **Generalization**: Models often fail outside the training distribution.

DADS simplifies this by learning **skill-conditioned dynamics**, which are easier to model due to reduced variability.

### Hierarchical RL (HRL)
HRL methods (Bacon et al., 2017; Vezhnevets et al., 2017) decompose tasks into **high-level policies** and **low-level skills**. However:
- End-to-end HRL is prone to instability.
- Skills are often task-specific, limiting reuse.

DADS provides **task-agnostic skills** that can be composed via model-based planning, avoiding end-to-end training pitfalls.

---
## Method

### Overview
DADS consists of two phases:
1. **Unsupervised skill discovery**: Learn a skill-conditioned policy **π(a|s, z)** and skill-dynamics model **qφ(s′|s, z)**.
2. **Zero-shot planning**: Use **model-predictive control (MPC)** to compose skills for downstream tasks.

### Objective: Mutual Information Maximization
DADS maximizes the **conditional mutual information** between the next state **s′** and skill **z** given the current state **s**:
\[
I(s'; z | s) = H(s'|s) - H(s'|s, z)
\]
- **H(s′|s)**: Maximizes **diversity** of transitions.
- **H(s′|s, z)**: Minimizes **uncertainty** (maximizes predictability) of transitions for a given skill.

### Variational Lower Bound
The objective is intractable due to unknown dynamics **p(s′|s, z)**. DADS uses a variational lower bound:
\[
I(s'; z | s) \geq \mathbb{E}_{z,s,s' \sim p} \left[ \log q_\phi(s'|s, z) \right] - \mathbb{E}_{s,z \sim p} \left[ D_{KL}(p(s'|s, z) || q_\phi(s'|s, z)) \right]
\]
- **First term**: Maximizes likelihood of transitions under the skill-dynamics model **qφ**.
- **Second term**: Minimizes KL divergence between true and learned dynamics (tightened via gradient descent).

### Intrinsic Reward
The policy **π** is trained with an intrinsic reward derived from the lower bound:
\[
r_z(s, a, s') = \log q_\phi(s'|s, z) - \log \hat{p}(s'|s)
\]
where \(\hat{p}(s'|s)\) is approximated by marginalizing **qφ** over skills sampled from the prior **p(z)**.

### Algorithm
DADS alternates between:
1. **Fitting skill-dynamics (qφ)**: Minimize \(D_{KL}(p(s'|s, z) || q_\phi(s'|s, z))\) via gradient descent.
2. **Updating policy (π)**: Maximize intrinsic reward using **Soft Actor-Critic (SAC)**.

![Figure 1: DADS framework. The agent interacts with the environment to produce transitions. The intrinsic reward is computed by comparing the transition probability under the skill-dynamics model (qφ) to random samples from the prior.](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-2-0.png)

---
## Experiments & Results

### Qualitative Analysis
DADS discovers diverse, stable skills across high-dimensional environments (e.g., **Humanoid**, **Ant**, **Half-Cheetah**) without extrinsic rewards. Skills include:
- **Locomotion primitives**: Forward/backward running, turning, jumping.
- **Stable gaits**: Avoids unstable behaviors (e.g., flipping) due to predictability constraints.

![Figure 4: Skills learned on MuJoCo environments. DADS discovers diverse locomotion primitives (e.g., walking, running, turning) without rewards.](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-1.png)

### Continuous vs. Discrete Skills
DADS supports **continuous skill spaces**, enabling:
- **Smooth interpolation** between behaviors (e.g., blending walking directions).
- **Higher diversity** compared to discrete skills (demonstrated in **Ant** environment).

![Figure 5: (Left) X-Y traces of Ant skills in continuous (smooth, diverse) vs. discrete (limited) spaces. (Right) Heatmap showing semantic meaning in the continuous latent space.](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-5-2.png)

### Skill Variance Analysis
DADS skills exhibit **lower variance** than prior methods (e.g., DIAYN), improving composability for hierarchical control.

![Figure 6: (Top-Left) Standard deviation of Ant’s position over time. DADS skills (blue/green) are significantly more stable than DIAYN (red).](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-7-2.png)

### Model-Based RL Comparison
DADS outperforms state-of-the-art MBRL baselines (e.g., PETS) in **zero-shot planning** for goal-directed navigation:
- **Random-MBRL**: Trained on random trajectories (no exploration).
- **Oracle-MBRL**: Trained with goal-directed exploration (unfair advantage).
- **DADS**: Uses only mutual-information-based exploration but generalizes better.

![Figure 7: (Left) DADS (continuous/discrete skills) outperforms MBRL baselines in Ant navigation. (Right) DADS generalizes to new tasks without fine-tuning.](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-8-1.png)

### Hierarchical Control
DADS skills enable **hierarchical composition** via MPC, outperforming:
- **Hierarchical DIAYN**: Fails due to high-variance skills.
- **Goal-Conditioned RL**: Struggles with sparse rewards and long horizons.

![Figure 8: (Left) Meta-controller succeeds with DADS skills but fails with DIAYN. (Right) DADS handles sparse rewards better than goal-conditioned RL.](/Users/omtg/Code/Web/ResearchWiki/backend/app/assets/pages/DYNAMICS-AWARE UNSUPERVISED DISCOVERY OF SKILLS_images/DYNAMICS-AWARE-UNSUPERVISED-DISCOVERY-OF-SKILLS.pdf-9-0.png)

---
## Conclusion

### Summary
DADS introduces a **two-phase framework** for unsupervised skill discovery:
1. **Skill Learning**: Discover predictable, diverse skills via mutual information maximization.
2. **Zero-Shot Planning**: Compose skills using model-predictive control for downstream tasks.

### Key Advantages
- **Scalability**: Works in high-dimensional state spaces (e.g., **Humanoid** with 376D state).
- **Generalization**: Skills transfer to unseen tasks without fine-tuning.
- **Efficiency**: Outperforms MBRL and HRL baselines in sample efficiency and stability.

### Future Work
- Extend to **off-policy data** (e.g., via relabeling tricks).
- Apply to **vision-based domains** (e.g., manipulation from pixels).
- Explore **more sophisticated planners** (e.g., uncertainty-aware MPC).

---
## References

- Abadi, M., Agarwal, A., et al. (2015). *TensorFlow: Large-scale machine learning on heterogeneous systems*.
- Achiam, J., Edwards, H., et al. (2018). *Variational option discovery algorithms*. arXiv:1807.10299.
- Bacon, P.-L., Harb, J., & Precup, D. (2017). *The option-critic architecture*. AAAI.
- Bellemare, M., et al. (2016). *Unifying count-based exploration and intrinsic motivation*. NeurIPS.
- Brockman, G., et al. (2016). *OpenAI Gym*. arXiv:1606.01540.
- Chua, K., et al. (2018). *Deep reinforcement learning in a handful of trials using probabilistic dynamics models*. NeurIPS.
- Eysenbach, B., et al. (2018). *Diversity is all you need: Learning skills without a reward function*. arXiv:1802.06070.
- Florensa, C., Duan, Y., & Abbeel, P. (2017). *Stochastic neural networks for hierarchical reinforcement learning*. arXiv:1704.03012.
- Gregor, K., Rezende, D. J., & Wierstra, D. (2016). *Variational intrinsic control*. arXiv:1611.07507.
- Haarnoja, T., et al. (2018). *Soft actor-critic: Off-policy maximum entropy deep reinforcement learning*. arXiv:1801.01290.
- Hausman, K., et al. (2018). *Learning an embedding space for transferable robot skills*. ICLR.
- Houthooft, R., et al. (2016). *Curiosity-driven exploration in deep reinforcement learning via Bayesian neural networks*. arXiv:1605.09674.
- Kumar, V., Todorov, E., & Levine, S. (2016). *Optimal control with learned local models: Application to dexterous manipulation*. ICRA.
- Nagabandi, A., et al. (2018). *Neural network dynamics for model-based deep reinforcement learning with model-free fine-tuning*. ICRA.
- Oudeyer, P.-Y., & Kaplan, F. (2009). *What is intrinsic motivation? A typology of computational approaches*. Frontiers in Neurorobotics.
- Pathak, D., et al. (2017). *Curiosity-driven exploration by self-supervised prediction*. ICML.
- Schulman, J., et al. (2017). *Proximal policy optimization algorithms*. arXiv:1707.06347.
- Sutton, R. S., Precup, D., & Singh, S. (1999). *Between MDPs and semi-MDPs: A framework for temporal abstraction in reinforcement learning*. Artificial Intelligence.
- Vezhnevets, A. S., et al. (2017). *Feudal networks for hierarchical reinforcement learning*. ICML.
- Williams, G., et al. (2016). *Aggressive driving with model predictive path integral control*. ICRA.