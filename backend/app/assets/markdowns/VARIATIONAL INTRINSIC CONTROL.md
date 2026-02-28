# VARIATIONAL INTRINSIC CONTROL

## Abstract

In this paper, we introduce a new unsupervised reinforcement learning method for discovering the set of intrinsic options available to an agent. This set is learned by maximizing the number of different states an agent can reliably reach, as measured by the mutual information between the set of options and option termination states. To this end, we instantiate two policy gradient-based algorithms, one that creates an explicit embedding space of options and one that represents options implicitly. The algorithms also provide an explicit measure of empowerment in a given state that can be used by an empowerment-maximizing agent. The algorithm scales well with function approximation and we demonstrate the applicability of the algorithm on a range of tasks.

## Introduction

In this paper, we aim to provide an answer to the question of what _intrinsic_ options are available to an agent in a given state—that is, options that meaningfully affect the world. We define options as policies with a termination condition and are primarily concerned with their consequences—what states in the environment they reach upon termination. The set of all options available to an agent is independent of an agent’s intentions—it is the set of all things that are possible for an agent to achieve. The purpose of this work is to provide an algorithm that aims to discover as many intrinsic options as it can, using an information-theoretic learning criterion and training procedure.

This differs from the traditional approach to option learning where the goal is to find a small number of options that are useful for a particular task. Limiting oneself to working with relatively small option spaces makes both credit assignment and planning over long time intervals easier. However, we argue that operating on the larger space of intrinsic options, as alluded to above, is in fact useful even though the space is vastly larger. First, the number of options is still much smaller than the number of all action sequences, since options are distinguished in terms of their final states, and many action sequences can reach the same state. Second, we aim to learn good representational embeddings of these options, where similar options are close in representational space and where we can rely on the power of generalization. In such embedded spaces, a planner needs only choose a neighborhood of this space containing options that have sufficiently similar consequences.

The idea of goal and state embeddings, along with a universal value function for reaching these goals, was introduced in Schaul et al. (2015). This work allowed an agent to efficiently represent control over many goals and to generalize to new goals. However, the goals were assumed to be given. This paper extends that work and provides a mechanism for learning goals (options) while preserving their embedded nature.

There are at least two scenarios where our algorithm can be useful. One is the classical reinforcement learning case that aims to maximize an externally provided reward, as we explained above. In this case, rather than learning options to uniformly represent control, the agent can combine extrinsic reward with an intrinsic control maximization objective, biasing learning towards high reward options.

The second scenario is that in which the long-term goal of the agent is to get to a state with a maximal set of available intrinsic options—the objective of _empowerment_. This set of options consists of those that the agent knows how to use. Note that this is not the theoretical set of all options: it is of no use to the agent that it is possible to do something if it is unable to learn how to do it. Thus, to maximize empowerment, the agent needs to simultaneously learn how to control the environment as well—it needs to discover the options available to it. The agent should in fact not aim for states where it has the most control according to its current abilities, but for states where it expects it will achieve the most control _after_ learning. Being able to learn available options is thus fundamental to becoming empowered.

Let us compare this to the commonly used intrinsic motivation objective of maximizing the amount of model-learning progress, measured as the difference in compression of its experience before and after learning. The empowerment objective differs from this in a fundamental manner: the primary goal is not to understand or predict the observations but to control the environment. This is an important point—agents can often control an environment perfectly well without much _understanding_, as exemplified by canonical model-free reinforcement learning algorithms, where agents only model action-conditioned expected returns. Focusing on such understanding might significantly distract and impair the agent, as such reducing the control it achieves.

Our algorithm can be viewed as learning to represent the intrinsic control space of an agent. Developing this space should be seen as acquiring universal knowledge useful for accomplishing a multitude of different tasks, such as maximizing extrinsic or intrinsic reward. This is analogous to unsupervised learning in data processing, where the goal is to find representations of data that are useful for other tasks. The crucial difference here, however, is that rather than simply finding representations, we learn explicit policies that an agent can choose to follow. Additionally, the algorithm explicitly estimates the amount of control it has in different states—intuitively, the total number of reliably reachable states—and can as such be used for an empowerment maximizing agent.

A most common criterion for unsupervised learning is data likelihood. For a given data set, various algorithms can be compared based on this measure. No such commonly established measure exists for the comparison of unsupervised learning performance in agents. One of the primary difficulties is that in unsupervised learning the data is known, but in control, an agent exists in an environment and needs to act in it in order to discover what states and dynamics it contains. Nevertheless, we should be able to compare agents in terms of the amount of intrinsic control and empowerment they achieve in different states. Just like there are multiple methods and objectives for unsupervised learning, we can devise multiple methods and objectives for unsupervised control. Data likelihood and empowerment are both information measures: likelihood measures the amount of information needed to describe data and empowerment measures the mutual information between action choices and final states. Therefore, we suggest that what maximum likelihood is to unsupervised learning, mutual information between options and final states is to unsupervised control.

This information measure has been introduced in the empowerment literature before along with methods for measuring it. Recently, Mohamed & Rezende (2015) proposed an algorithm that can utilize function approximation and deep learning techniques to operate in high-dimensional environments. However, this algorithm considers the mutual information between sequences of actions and final states. This corresponds to maximizing the empowerment over _open loop_ options, where the agent _a priori_ decides on a sequence of actions in advance, and then follows these regardless of (potentially stochastic) environment dynamics. Obviously, this often limits performance severely as the agent cannot properly react to the environment, and it tends to lead to a significant underestimation of empowerment. In this paper, we provide a new perspective on this measure, and instantiate two novel algorithms that use _closed loop_ options where actions are conditioned on state. We show, on a number of tasks, that we can use these to both significantly increase intrinsic control and improve the estimation of empowerment.

## 2 INTRINSIC CONTROL AND THE MUTUAL INFORMATION PRINCIPLE

In this section, we explain how we represent intrinsic options and the corresponding objective we optimize.

We define an option as an element Ω of a space and an associated policy _π_ ( _a|s,_ Ω) that chooses an action _a_ in a state _s_ when following Ω. The policy _π_ has a special _termination_ action that terminates the option and yields a final state _sf_. Now let us consider the following example spaces for Ω. 1) Ω takes a finite number of values Ω _∈{_ 1 _, . . ., n}_. This is the simplest case in which for each _i_ a separate policy _πi_ is followed. 2) Ω is a binary vector of length _n_. This captures a combinatorial number 2 _[n]_ of possibilities. 3) Ω _∈_ _R_ _[d]_ is a d-dimensional real vector. Here the space of options is infinite. It is expected that policies for nearby Ωs will be similar in practice.

We need to express the knowledge about which regions of option space to consider. Imagine we start in a state _s_ 0 and follow an option Ω. As environments and policies are typically stochastic, we might terminate at different final states at different times. The policy thus defines a probability distribution _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω). Now consider two different options. If they lead to very similar states, they should inherently, intrinsically, not be seen as different from one another. So how do we express our knowledge regarding the effective intrinsic option set in a given state?

To help answer this question, consider an example of a discrete option case with three options Ω1 _,_ Ω2 _,_ Ω3. Assume that Ω1 always leads to a state _s_ 1 while both Ω2 and Ω3 always lead to a state _s_ 2. Then we would like to say that we really have two _intrinsic_ options: Ω1 and (Ω2 _,_ Ω3). If we were to sample these options in order to maximize behavior diversity we would half of the time choose Ω1 and half of the time any one of Ω2 _,_ Ω3. The relative choice frequencies of Ω2 and Ω3 do not matter in this example. We express these choices by a probability distribution _p_ _[C]_ (Ω _|s_ 0) which we call the controllability distribution.

Intuitively, to maximize intrinsic control we should choose Ωs that maximize the diversity of final states while, for given Ω, controlling as precisely as possible what the ensuing final states are. The former can be expressed mathematically as entropy _H_ ( _sf_ ) = _−_ [�] _sf_ _[p]_ [(] _[s][f]_ _[|][s]_ [0][) log] _[ p]_ [(] _[s][f]_ _[|][s]_ [0][)] [where]

_p_ ( _sf_ _|s_ 0) = [�] Ω _[p][J]_ [(] _[s][f]_ _[|][s]_ [0] _[,]_ [ Ω)] _[p][C]_ [(Ω] _[|][s]_ [0][)][.] [The latter, for a given][ Ω][, can be expressed as the negative]

log probability _−_ log _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) (the number of bits needed to specify the final state given Ω) which then needs to be averaged over Ω and _sf_. Subtracting these two quantities yields the objective we wish to optimize - the mutual information _I_ (Ω _, sf_ _|s_ 0) between options and final states under probability distribution _p_ (Ω _, sf_ _|s_ 0) = _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) _p_ _[C]_ (Ω _|s_ 0):

_I_ (Ω _, sf_ _|s_ 0)= _−_

_p_ ( _sf_ _|s_ 0) log _p_ ( _sf_ _|s_ 0) +
_sf_ Ω _,sf_

- _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) _p_ _[C]_ (Ω _|s_ 0) log _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) _,_ (1)

Ω _,sf_

= _−_

_p_ _[C]_ (Ω _|s_ 0) log _p_ _[C]_ (Ω _|s_ 0) +
Ω Ω _,sf_

- _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) _p_ _[C]_ (Ω _|s_ 0) log _p_ (Ω _|s_ 0 _, sf_ ) _._ (2)

Ω _,sf_

The mutual information is symmetric and the second line contains its reverse expression. This expression has a very intuitive interpretation associated with it: we should be able to tell options apart if we can infer them from final states. That is, if for two options Ω1 and Ω2, upon reaching state _sf_ 1, we can infer it was option Ω1 that was executed rather than Ω2, and when reaching a state _sf_ 2 we can infer it was option Ω2 rather than Ω1, then Ω1 and Ω2 can be said to be _intrinsically_ different options. We would like to maximize the set of options – achieve a large entropy of _p_ (Ω _|s_ 0) (the first term of (2)). At the same time we wish to make sure these options achieve intrinsically different goals - that is, that they can be inferred from their final states. This entails maximizing log _p_ (Ω _|s_ 0 _, sf_ ), the average of which is the second term of (2).

The advantage of this formulation is the absence of the term _p_ ( _sf_ _|s_ 0) in the formulation, which is difficult to obtain as we would have to integrate over Ω. In rewriting the derivation, however, the term _p_ (Ω _|s_ 0 _, sf_ ) was introduced, which we arrived at from _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) _p_ _[C]_ (Ω _|s_ 0) using Bayes’ rule. The quantity _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) is inherent to the environment, but obtaining Bayes’ reverse _p_ (Ω _|s_ 0 _, sf_ ) is difficult. However, it has an interpretation as a prediction of Ω from final state _sf_. It would be fortuitous if we could train a separate function approximator to infer this quantity. Fortunately, this is exactly what the variational bound (Mohamed & Rezende, 2015) provides (see Appendix 1 for derivation):

_I_ _[V B]_ (Ω _, sf_ _|s_ 0) = _−_

_p_ _[C]_ (Ω _|s_ 0) log _p_ _[C]_ (Ω _|s_ 0) +
Ω Ω _,sf_

- _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω) _p_ _[C]_ (Ω _|s_ 0) log _q_ (Ω _|s_ 0 _, sf_ ) (3)

Ω _,sf_

where _q_ is an option inference function which can be an arbitrary distribution, and we have _I_ _≥_ _I_ _[V B]_. In this paper, we train both the parameters of _p_ _[C]_ (Ω _|s_ 0), _q_ (Ω _|s_ 0 _, sf_ ) and the parameters of policy _π_ ( _a|s,_ Ω) (which determines _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω)) to maximize _I_ _[V B]_.

## 3 INTRINSIC CONTROL WITH EXPLICIT OPTIONS

In this section, we provide a simple algorithm to maximize the variational bound introduced above. Throughout we assume we have distributions, policies, and other possible functions parameterized using recent function approximation techniques such as neural networks, and state representations are formed from observations using recurrent neural networks. However, we only calculate the mutual information between options and final observations instead of final states, and leave the latter for future work. Algorithm 1 provides an outline of the basic training loop.

**Algorithm 1** Intrinsic Control with Explicit Options

Assume an agent in a state _s_ 0
**for** episode = 1 _, M_ **do**

Sample Ω _∼_ _p_ _[C]_ (Ω _|s_ 0)
Follow policy _π_ ( _a|_ Ω _, s_ ) till termination state _sf_
Regress _q_ (Ω _|s_ 0 _, sf_ ) towards Ω
Calculate intrinsic reward _rI_ = log _q_ (Ω _|s_ 0 _, sf_ ) _−_ log _p_ _[C]_ (Ω _|s_ 0)
Use a reinforcement learning algorithm update for _π_ ( _a|_ Ω _, s_ ) to maximize _rI_.
Reinforce option prior _p_ _[C]_ (Ω _|s_ 0) based on _rI_.
Set _s_ 0 = _sf_
**end for**
Note: Empowerment at _s_ is estimated by the reinforce baseline of _p_ _[C]_, which tracks _rI_.

This algorithm is derived from (3) in Appendix 2. Note again that _π_ appears in (3) by determining the distribution of terminal states _p_ _[J]_ ( _sf_ _|s_ 0 _,_ Ω). Here we give an intuitive explanation of the algorithm. In a state _s_ 0 an agent tries an option Ω from its available options _p_ _[C]_ (Ω _|s_ 0). Its goal is to choose actions that lead to a state _sf_ from which this Ω can be inferred as well as possible using option inference function _q_ (Ω _|s_ 0 _, sf_ ). If it can infer this option well, then it means that other options don’t lead to this state very often, and therefore this option is intrinsically different from others. This goal is expressed as the intrinsic reward _rI_ (discussed in the next paragraph). The agent can use any reinforcement learning algorithm (Sutton & Barto, 1998), such as policy gradients (Williams, 1992) or _Q_ -learning (Watkins, 1989; Werbos, 1977), to train a policy to maximize this reward. In the final state, it updates its option inference function _q_ towards the actual Ω chosen (by taking the gradient of log _q_ (Ω _|s_ 0 _, sf_ )). It also reinforces the prior _p_ _[C]_ based on this reward – if the reward were high, it should choose this option more often. Note that we can also keep prior _p_ _[C]_ fixed, for example to the uniform Gaussian distribution. Then, different values of Ω will result in different behavior through learning.

The intrinsic reward _rI_ equals, on average, the logarithm of the number of different options an agent has in a given state - that is, the empowerment in that state. This follows from the definition of mutual information (3) – it is the expression we get when we take a sample of Ω and _sf_. However, we also provide an intuitive explanation. The log _p_ _[C]_ (Ω _|s_ 0) is essentially the negative logarithm of the number of different Ωs we can choose (for the continuous case, imagine finely discretizing). However, not all Ωs do different things. The region where _q_ (Ω _|s_ 0 _, sf_ ) is large defines a region of similar options. The empowerment essentially equals the number of such regions in the total region given by _p_ _[C]_. Taking the logarithm of the ratio of the total number of options _∼_ 1 _/p_ _[C]_ to the number of options within a region _∼_ 1 _/q_ gives us log _q/p_ _[C]_ = log _q −_ log _p_ _[C]_ = _rI_.

We train _p_ _[C]_ using policy gradients (Williams, 1992). During training we estimate a baseline to lower the variance of weight updates (see Appendix 2). This baseline tracks the expected return in a given state – intrinsic reward in this case, which equals the empowerment. As such, the algorithm actually yields an explicit empowerment estimate.

### 3.1 EXPERIMENTS

#### 3.1.1 GRID WORLD

We demonstrate the behavior of the algorithm on a simple example of a two-dimensional grid world. The agent lives on a grid and has five actions – it can move up, down, right, left and stay put. The environment is noisy in the following manner: after an agent takes a step, with probability 0 _._ 2 the agent is pushed in a random direction. We follow Algorithm 1. We choose Ω to be a discrete space of _N_ = 30 options. We fix the option prior _p_ _[C]_ to be uniform (over 30 values). The goal is therefore to learn a policy _π_ ( _a|s,_ Ω) that would make the 30 options end at as different states as possible. This is measured by the function _q_ (Ω _|sf_ ) which, from the state _sf_ reached, tries to infer which option Ω was followed. At the end of an episode we get an intrinsic reward _rI_ = _−_ log _p_ + log _q_ = log _N_ + log _q_ (log _N_ because _p_ _[C]_ = 1 _/N_ is fixed). If a particular option is inferred correctly and with confidence, then log _q_ will be close to zero and negative, and the reward will be large ( _≈_ log _N_ ). If it is wrong, however, then log _q_ will be very negative and the reward small. As we are choosing options at random (from the uniform _p_ _[C]_ ), in order to get a large reward on average, different options need to reach substantially different states in order for the _q_ to be able to infer the chosen option. In a grid world we can plot at which locations a given option is inferred by _q_, which are the locations to which the option navigates. This is shown in the Figure 1 top, with each rectangle corresponding to a different option, and the intensity denoting the probability of predicting a given option. Thus, we see that indeed, different options learn to navigate to different, localized places in the environment.

In this example, we use Q-learning to learn the policy. In general we can express the Q function for a set of _N_ different options by running the corresponding input states through a neural network and outputting _N_ _× nactions_ values, one for each option and action. This way, we can update _Q_ of all the options at the same time efficiently, on a triplet of experience _st, at, st_ +1. In this experiment we use a linear function approximator, and terminate options with fixed probability 1 _−_ _γ_ = 0 _._ 05. We could also use a universal value function approximation (Schaul et al., 2015). For continuous option spaces we can still calculate the _Q_ by passing an input through a neural network, but then update the result on several, randomly sampled options Ω at the same time. Such an option space is then an option embedding in itself.

Figure 1: **Learning** **to** **navigate** **through** **a** **grid** **world.** **Left** : Standard grid world with valid actions indicated by green arrows (left, right, up, down) and by a green disc (do nothing). **Right** : Each square corresponds to a different option, and shows the probability of predicting this option at different locations in the environment. The negative logarithm of these values is proportional to the intrinsic reward that a given option is trying to maximize, and therefore the locations with large intensity show the locations where a given option terminates.

![Figure 1](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp69wytv3b.pdf-4-0.png)

#### 3.1.2 ’DANGEROUS’ GRID WORLD

The second environment is also a grid world, but with special properties. It consists of two parts: a narrow corridor connected to an open square (see figure 2, top-left), blue denoting the walls. However the square is not just a simple grid world, but is somewhat _dangerous_. There are two types of cells arranged as a checkerboard lattice (as on a chess board). On one sub-lattice, only the left and right actions actually move the agent to the adjacent states and on the other sub-lattice only the up and down actions do. If the agent picks an action that is not one of these, it falls into a state

![Figure 2](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp69wytv3b.pdf-5-0.png)

Figure 2: **Learning** **to** **navigate** **through** **a** **grid** **world** **with** **trap** **states.** **Left** : Dangerous grid world where cells on different checkerboard sub-lattices have different sets of valid actions (green arrows). Taking the wrong actions (red arrows and red disc) teleports the agent to the top-left corner indicated by a cross, from which there is only a small probability of escaping at each time step. The blue region represents a barrier, forming a narrow corridor on the top left. Furthermore, when a valid action is taken, with some probability the agent actually does not move. Therefore if the agent commits to a sequence of actions, it will quickly lose track as to which sub-lattice it is on, and fall into the low empowerment top left corner state. On the other hand, if it observes the environment it can always take actions to safely navigate the square. **Bottom:** Classical empowerment, which considers the effect of (open loop) action sequences, has very small empowerment inside the square because each sequence does not respond to changes due to environment noise and the agent instead prefers to sit in the ‘safe’ top left corridor. This is demonstrated in the bottom figure, which shows the exact empowerment at different locations for action sequence lengths 1 _, . . .,_ 6. We see that not only does the square area have low empowerment, but that the amount of empowerment goes down with increasing sequence length. With closed loop policies, on the other hand, the agent has learned to navigate to different locations of the square, as shown in the top right figure.

#### 3.2 THE IMPORTANCE OF CLOSED LOOP POLICIES

Classical empowerment (Salge et al., 2014; Mohamed & Rezende, 2015) maximizes mutual information between sequences of actions _A_ = _a_ 1 _, . . ., aT_ and final states. That is, it maximizes the same objective function (3), but where Ω= _A_. This corresponds to maximizing empowerment over the space of open loop options. That is, options where an agent first commits to a sequence of actions and then blindly follows this sequence regardless of what the environment does. In contrast, in a closed-loop option every action is conditioned on the current state. We show that using open-loop options can lead to severe underestimation of empowerment in stochastic environments, resulting in agents that aim to reach low-empowerment states.

We demonstrate this effect in the ’dangerous grid world’ environment, section 3.1.2. When using open loop options of length _T_, an agent at the center of the environment would have exponentially growing probability of being reset as a function of the option length _T_, resulting in an estimation of empowerment that quickly decreases with the option length, having its highest value inside the corridor at the top-left corner as shown in Figure 1 (bottom). A consequence of this is that such an agent would prefer being inside the corridor at the top-left corner, away from the center of the grid world.

In great contrast to the open loop case, when using closed loop options the empowerment will _grow_ _quadratically with the option length_, resulting in agents that prefer staying at the center of the grid world.

While this example might seem contrived, it is actually quite ubiquitous in the real world. For example, we can navigate around a city, whether walking or driving, quite safely. If we instead committed to a sequence of actions ahead, we would almost certainly be run over by a car, or if driving, crash into another car. The importance of the closed loop nature of policies is indeed well understood. What we have demonstrated here is that one should not use open loop policies even to measure empowerment.

#### 3.3 ADVANTAGES AND DISADVANTAGES

The advantages of Algorithm 1 are: 1) It is relatively simple, 2) it uses closed loop policies, 3) it can use general function approximation, 4) it is naturally formulated with combinatorial options spaces, both discrete and continuous and 5) it is model-free.

The primary problem we found with this algorithm is that it is difficult to make it work in practice with function approximation. We suggest there might be two reasons for this. First, the intrinsic reward is noisy and changing as the agent learns. This makes it difficult for the policy to learn. The algorithm worked as specified in those simple environments above when we used linear function approximation and a small, finite number of options. However, it failed when neural networks were substituted. We still succeeded by fixing the intrinsic reward for a period of time while learning the policy and vice versa. However, replacing the small option space by a continuous one made training even more difficult and only some runs succeeded. These problems are related to those in deep reinforcement learning (Mnih et al., 2015), where in order to make _Q_ learning work well with function approximation, one needs to store a large number of experiences in memory and replay them. It is possible that more work in this direction would find good practices for training this algorithm with general function and distribution approximations.

The second problem is exploration. If the agent encounters a new state, it should like to go there, because it might correspond to some new option it hasn’t considered before and therefore increase its control. However, when it gets there, the option inference function _q_ has not learned it yet. It is likely inferring the incorrect option, therefore giving a low reward and therefore discouraging the agent from going there. While the overall objective is maximized when the agent has the most control, the algorithm has difficulty maximizing this objective because two functions – the intrinsic reward and the policy – have to match up. It does a good job of expressing what the options are in a region it is familiar with, but it seems to fail to push into new state regions. Hence, we introduce a new algorithm formulation in section 4 to address these issues.

## 4 INTRINSIC CONTROL WITH IMPLICIT OPTIONS

To address the learning difficulties of Algorithm 1 we use the action space itself as the option space. This gives the inference function _q_ grounded targets which makes it easier to train. Having a sensible _q_ makes the policy easier to train. The elements of the algorithm are as follows. The controllability prior _p_ _[C]_ and policy _π_ in Algorithm 1 simply become a policy, which we denote by _π_ _[p]_ ( _at|s_ _[p]_ _t_ [)][.] [The]
_s_ _[p]_ _t_ [is an internal state that is calculated from][ (] _[s]_ _t_ _[p]_ _−_ 1 _[, x][t][, a][t][−]_ [1][)][.] [In our implementation it is the state]
of a recurrent network. The _q_ function in Algorithm 1 should infer the action choices made by _π_ _[p]_ knowing the final observation _xf_ and thus becomes _q_ = _π_ _[q]_ ( _at|s_ _[q]_ _t_ [)] [where] _[s][q]_ [is] [its] [internal] [state]
calculated from ( _s_ _[q]_ _t−_ 1 _[, x][t][, a][t][−]_ [1] _[, x][f]_ [)][.] [The] [logarithm] [of] [the] [number] [of] [action] [choices] [at] _[t]_ [that] [are]
effectively different from each other – that can be distinguished based on the observation of the final state _xf_ - is given by _rI,t_ = log _π_ _[q]_ ( _at|s_ _[q]_ _t_ [)] _[ −]_ [log] _[ π][p]_ [(] _[a][t][|][s][p]_ _t_ [)][.] [We] [now] [introduce] [an] [algorithm] [that]
will maximize the expected cumulative number of distinct actions by maximizing the intrinsic return
_RI_ = [�] _t_ _[r][I,t]_ [ in algorithm 2.]

In this setting, maximization of control is substantially simplified. Consider an experience
_x_ 0 _, a_ 0 _, . . ., xf_ generated by some policy. The learning of _π_ _[q]_ is a supervised learning problem of inferring the action choices that led to _xf_. Even the random action policy terminates at different states, and thus _π_ _[q]_ is able to train on such experiences, mimicking decisions that happen to lead to _xf_. The _π_ _[p]_ can be thought of as choosing among those _π_ _[q]_ that lead to diverse states, which in

![Figure 3](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp69wytv3b.pdf-8-0.png)

![Figure 3](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp69wytv3b.pdf-8-1.png)

![Figure 3](/app/app/assets/pages/VARIATIONAL INTRINSIC CONTROL_images/tmp69wytv3b.pdf-8-2.png)

Figure 3: **Intrinsic Control with Implicit Options.** **Left and Center** : The environment is a four room 25 _×_ 25 grid world. Left: Blue denotes the beginning of a trajectory and green the end. The algorithm learns trajectories that extend through the environment and accurately pass through the doors between rooms. Center: Green shows the distribution of end points for trajectories of length 25. A trajectory in a given square starts at a location (3 _x_ + 1 _,_ 3 _y_ + 1) where ( _x, y_ ) denotes the coordinates of the room in the picture. We see that the end points cover the reachable set of points nearly uniformly. **Right** : Each column shows