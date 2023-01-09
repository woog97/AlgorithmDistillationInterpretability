
from dataclasses import dataclass


@dataclass
class DTArgs:
    exp_name: str = "Dev"
    trajectory_path: str = "trajectories/MiniGrid-MultiRoom-N4-S5-v0916b26d8-9f9b-4a5f-b88f-665602e08f59.pkl"
    d_model: int = 64
    n_heads: int = 2
    d_mlp: int = 128
    n_layers: int = 2
    learning_rate: float = 0.00025
    batch_size: int = 128
    batches: int = 3
    max_len: int = 100
    pct_traj: float = 1.0
    weight_decay: float = 0.1
    seed: int = 1
    track: bool = True
    wandb_project_name: str = "DecisionTransformerInterpretability"
    wandb_entity: str = None
    test_frequency: int = 100
    test_batches: int = 10
    eval_frequency: int = 100
    eval_episodes: int = 1
    initial_rtg: float = 1
    eval_max_time_steps: int = 1000