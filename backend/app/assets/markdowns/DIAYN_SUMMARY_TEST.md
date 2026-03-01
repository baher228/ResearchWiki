# DIVERSITY IS ALL YOU NEED: LEARNING SKILLS WITHOUT A REWARD FUNCTION

## Abstract

This paper introduces "Diversity is All You Need" (DIAYN), a method for learning useful skills without a reward function. The proposed method maximizes an information-theoretic objective using a maximum entropy policy. On various simulated robotic tasks, DIAYN demonstrates the emergence of diverse skills, such as walking and jumping, without supervision. The method also shows that pretrained skills can serve as effective parameter initializations for downstream tasks and can be composed hierarchically to solve complex, sparse reward tasks. The results suggest that unsupervised discovery of skills can be an effective pretraining mechanism for overcoming challenges in exploration and data efficiency in reinforcement learning.

## Introduction

Deep reinforcement learning (RL) has successfully learned reward-driven skills in various domains, including playing games, controlling robots, and navigating complex environments. However, intelligent creatures can explore and learn useful skills without supervision, which can be beneficial when faced with specific goals. Learning skills without reward has several practical applications, such as addressing challenges in exploration, serving as primitives for hierarchical RL, reducing the need for human feedback, and determining what tasks an agent should learn in unfamiliar environments. This paper presents a method for autonomous acquisition of useful skills without any reward signal, using a simple objective based on mutual information.

## Related Work

Previous work on hierarchical RL has focused on learning skills to maximize a single, known reward function by jointly learning a set of skills and a meta-controller. However, this approach can lead to degeneracy where the meta-policy does not select "bad" options, preventing them from receiving any reward signal to improve. DIAYN avoids this by using a random meta-policy during unsupervised skill-learning, ensuring that neither the skills nor the meta-policy aim to solve any single task.

Related work has also examined connections between RL and information theory, developing maximum entropy algorithms. DIAYN maximizes the mutual information between states and skills, which can be interpreted as maximizing the empowerment of a hierarchical agent whose action space is the set of skills.

Prior work in neuroevolution and evolutionary algorithms has studied how complex behaviors can be learned by directly maximizing diversity. DIAYN aims to acquire complex skills with minimal supervision to improve efficiency and as a stepping stone for imitation learning and hierarchical RL.

## Method

### How It Works

DIAYN builds on three ideas: skills should dictate the states visited, states should be used to distinguish skills, and skills should be as diverse as possible to encourage exploration. The objective is to maximize the mutual information between skills and states while minimizing the mutual information between skills and actions given the state. The method also maximizes the entropy of the mixture policy to ensure that states, not actions, are used to distinguish skills.

### Implementation

DIAYN is implemented using soft actor-critic (SAC), learning a policy conditioned on a latent variable. The policy's entropy over actions is maximized, and the expectation in the objective is replaced with a pseudo-reward derived from the discriminator. The discriminator is updated to better infer the skill from states visited, while the agent is rewarded for visiting states that are easy to discriminate.

### Stability

DIAYN forms a cooperative game, avoiding many instabilities of adversarial saddle-point formulations. Empirically, DIAYN is robust to random seed and has little effect on downstream tasks.

## Experiments

### Analysis of Learned Skills

DIAYN learns diverse skills on tasks of increasing complexity, ranging from 2 DOF point navigation to 111 DOF ant locomotion. The skills learned include walking, jumping, and various locomotion primitives. The diversity of the rewards increases throughout training, indicating that the skills become increasingly diverse.

### Harnessing Learned Skills

DIAYN skills can be used for downstream tasks, such as policy initialization, hierarchy, and imitation learning. Using learned skills for policy initialization accelerates learning. A simple extension to DIAYN for hierarchical RL outperforms competitive baselines on two challenging tasks. DIAYN skills can also be used for imitation learning, closely matching expert trajectories.

## Conclusion

DIAYN demonstrates the ability to learn diverse skills without reward functions, often solving benchmark tasks with one of the learned skills without actually receiving any task reward. The method can be used to quickly adapt to new tasks, solve complex tasks via hierarchical RL, and imitate an expert. The skills produced by DIAYN might be used by game designers to control complex robots and by artists to animate characters.

## References

- Achiam, J., Edwards, H., Amodei, D., & Abbeel, P. (2017). Variational autoencoding learning of options by reinforcement. _NIPS Deep Reinforcement Learning Symposium_.
- Barber, D., & Agakov, F. (2004). The im algorithm: a variational approach to information maximization. _Advances in Neural Information Processing Systems_, 16:201.
- Bacon, P. L., Harb, J., & Precup, D. (2017). The option-critic architecture. In _AAAI_, pp. 1726–1734.
- Baranes, A., & Oudeyer, P. Y. (2013). Active learning of inverse models with intrinsically motivated goal exploration in robots. _Robotics and Autonomous Systems_, 61(1):49–73.
- Bellemare, M., Srinivasan, S., Ostrovski, G., Schaul, T., Saxton, D., & Munos, R. (2016). Unifying count-based exploration and intrinsic motivation. In _Advances in Neural Information Processing Systems_, pp. 1471–1479.
- Bishop, C. M. (2016). _Pattern Recognition and Machine Learning_. Springer-Verlag New York.
- Brockman, G., Cheung, V., Pettersson, L., Schneider, J., Schulman, J., Tang, J., & Zaremba, W. (2016). Openai gym. _arXiv preprint arXiv:1606.01540_.
- Christiano, P. F., Leike, J., Brown, T., Legg, S., & Amodei, D. (2017). Deep reinforcement learning from human preferences. In _Advances in Neural Information Processing Systems_, pp. 4302–4310.
- Dayan, P., & Hinton, G. E. (1993). Feudal reinforcement learning. In _Advances in neural information processing systems_, pp. 271–278.
- Duan, Y., Chen, X., Schulman, J., & Abbeel, P. (2016). Benchmarking deep reinforcement learning for continuous control. In _International Conference on Machine Learning_, pp. 1329–1338.
- Florensa, C., Duan, Y., & Abbeel, P. (2017). Stochastic neural networks for hierarchical reinforcement learning. _arXiv preprint arXiv:1704.03012_.
- Frans, K., Ho, J., Chen, X., Abbeel, P., & Schulman, J. (2017). Meta learning shared hierarchies. _arXiv preprint arXiv:1710.09767_.
- Fu, J., Co-Reyes, J., & Levine, S. (2017). Ex2: Exploration with exemplar models for deep reinforcement learning. In _Advances in Neural Information Processing Systems_, pp. 2574–2584.
- Gregor, K., Jimenez Rezende, D., & Wierstra, D. (2016). Variational intrinsic control. _arXiv preprint arXiv:1611.07507_.
- Gu, S., Holly, E., Lillicrap, T., & Levine, S. (2017). Deep reinforcement learning for robotic manipulation with asynchronous off-policy updates. In _Robotics and Automation (ICRA), 2017 IEEE International Conference on_, pp. 3389–3396. IEEE.
- Hadfield-Menell, D., Milli, S., Abbeel, P., Russell, S. J., & Dragan, A. (2017). Inverse reward design. In _Advances in Neural Information Processing Systems_, pp. 6768–6777.
- Hausman, K., Springenberg, J. T., Wang, Z., Heess, N., & Riedmiller, M. (2018). Learning an embedding space for transferable robot skills. _International Conference on Learning Representations_.
- Heess, N., Wayne, G., Tassa, Y., Lillicrap, T., Riedmiller, M., & Silver, D. (2016). Learning and transfer of modulated locomotor controllers. _arXiv preprint arXiv:1610.05182_.
- Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., & Meger, D. (2017). Deep reinforcement learning that matters. _arXiv preprint arXiv:1709.06560_.
- Houthooft, R., Chen, X., Duan, Y., Schulman, J., De Turck, F., & Abbeel, P. (2016). Vime: Variational information maximizing exploration. In _Advances in Neural Information Processing Systems_, pp. 1109–1117.
- Jung, T., Polani, D., & Stone, P. (2011). Empowerment for continuous agent—environment systems. _Adaptive Behavior_, 19(1):16–39.
- Krishnan, S., Fox, R., Stoica, I., & Goldberg, K. (2017). Ddco: Discovery of deep continuous options for robot learning from demonstrations. In _Conference on Robot Learning_, pp. 418–437.
- Lehman, J., & Stanley, K. O. (2011a). Abandoning objectives: Evolution through the search for novelty alone. _Evolutionary computation_, 19(2):189–223.
- Lehman, J., & Stanley, K. O. (2011b). Evolving a diversity of virtual creatures through novelty search and local competition. In _Proceedings of the 13th annual conference on Genetic and evolutionary computation_, pp. 211–218. ACM.
- Merton, R. K. (1968). The matthew effect in science: The reward and communication systems of science are considered. _Science_, 159(3810):56–63.
- Mirowski, P., Pascanu, R., Viola, F., Soyer, H., Ballard, A. J., Banino, A., ... & Kavukcuoglu, K. (2016). Learning to navigate in complex environments. _arXiv preprint arXiv:1611.03673_.
- Mnih, V., Kavukcuoglu, K., Silver, D., Graves, A., Antonoglou, I., Wierstra, D., & Riedmiller, M. (2013). Playing atari with deep reinforcement learning. _arXiv preprint arXiv:1312.5602_.
- Mohamed, S., & Rezende, D. J. (2015). Variational information maximisation for intrinsically motivated reinforcement learning. In _Advances in neural information processing systems_, pp. 2125–2133.
- Mouret, J. B., & Doncieux, S. (2009). Overcoming the bootstrap problem in evolutionary robotics using behavioral diversity. In _Evolutionary Computation, 2009. CEC’09. IEEE Congress on_, pp. 1161–1168. IEEE.
- Murphy, K. P. (2012). _Machine Learning: A Probabilistic Perspective_. MIT Press.
- Nachum, O., Norouzi, M., Xu, K., & Schuurmans, D. (2017). Bridging the gap between value and policy based reinforcement learning. In _Advances in Neural Information Processing Systems_, pp. 2772–2782.
- Oudeyer, P. Y., Kaplan, F., & Hafner, V. V. (2007). Intrinsic motivation systems for autonomous mental development. _IEEE transactions on evolutionary computation_, 11(2):265–286.
- Pathak, D., Agrawal, P., Efros, A. A., & Darrell, T. (2017). Curiosity-driven exploration by self-supervised prediction. _arXiv preprint arXiv:1705.05363_.
- Pong, V., Gu, S., Dalal, M., & Levine, S. (2018). Temporal difference models: Model-free deep rl for model-based control. _arXiv preprint arXiv:1802.09081_.
- Ryan, R. M., & Deci, E. L. (2000). Intrinsic and extrinsic motivations: Classic definitions and new directions. _Contemporary educational psychology_, 25(1):54–67.
- Schulman, J., Levine, S., Jordan, M., & Abbeel, P. (2015a). Trust region policy optimization. In _International Conference on Machine Learning_, pp. 1889–1897.
- Schulman, J., Moritz, P., Levine, S., Jordan, M., & Abbeel, P. (2015b). High-dimensional continuous control using generalized advantage estimation. _arXiv preprint arXiv:1506.02438_.
- Schulman, J., Abbeel, P., & Chen, X. (2017). Equivalence between policy gradients and soft q-learning. _arXiv preprint arXiv:1704.06440_.
- Shazeer, N., Mirhoseini, A., Maziarz, K., Davis, A., Le, Q., Hinton, G., & Dean, J. (2017). Outrageously large neural networks: The sparsely-gated mixture-of-experts layer. _arXiv preprint arXiv:1701.06538_.
- Silver, D., Huang, A., Maddison, C. J., Guez, A., Sifre, L., Van Den Driessche, G., ... & Graepel, T. (2016). Mastering the game of go with deep neural networks and tree search. _nature_, 529(7587):484–489.
- Stanley, K. O., & Miikkulainen, R. (2002). Evolving neural networks through augmenting topologies. _Evolutionary computation_, 10(2):99–127.
- Such, F. P., Madhavan, V., Conti, E., Lehman, J., Stanley, K. O., & Clune, J. (2017). Deep neuroevolution: Genetic algorithms are a competitive alternative for training deep neural networks for reinforcement learning. _arXiv preprint arXiv:1712.06567_.
- Sukhbaatar, S., Lin, Z., Kostrikov, I., Synnaeve, G., Szlam, A., & Fergus, R. (2017). Intrinsic motivation and automatic curricula via asymmetric self-play. _arXiv preprint arXiv:1703.05407_.
- Woolley, B. G., & Stanley, K. O. (2011). On the deleterious effects of a priori objectives on evolution and representation. In _Proceedings of the 13th annual conference on Genetic and evolutionary computation_, pp. 957–964. ACM.
- Zhu, Y., Mottaghi, R., Kolve, E., Lim, J. J., Gupta, A., Fei-Fei, L., & Farhadi, A. (2017). Target-driven visual navigation in indoor scenes using deep reinforcement learning. In _Robotics and Automation (ICRA), 2017 IEEE International Conference on_, pp. 3357–3364. IEEE.
- Ziebart, B. D., Maas, A. L., Bagnell, J. A., & Dey, A. K. (2008). Maximum entropy inverse reinforcement learning. In _AAAI_, volume 8, pp. 1433–1438. Chicago, IL, USA.