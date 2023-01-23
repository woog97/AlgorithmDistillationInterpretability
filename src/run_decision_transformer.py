import torch as t
import warnings
import wandb
import time
import os

from environments import make_env

from decision_transformer.utils import DTArgs, parse_args
from decision_transformer.model import DecisionTransformer
from decision_transformer.offline_dataset import TrajectoryLoader
from decision_transformer.train import train


warnings.filterwarnings("ignore", category=DeprecationWarning)


if __name__ == "__main__":

    args = parse_args()
    args = DTArgs(
        exp_name=args.exp_name,
        seed=args.seed,
        cuda=args.cuda,
        track=args.track,
        wandb_project_name=args.wandb_project_name,
        wandb_entity=args.wandb_entity,
        trajectory_path=args.trajectory_path,
        pct_traj=args.pct_traj,
        d_model=args.d_model,
        n_heads=args.n_heads,
        d_mlp=args.d_mlp,
        n_layers=args.n_layers,
        layer_norm=args.layer_norm,
        linear_time_embedding=args.linear_time_embedding,
        n_ctx=args.n_ctx, # we set the context and then train on sequences of lenght n_ctx // 3. 
        batches=args.batches,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        batch_size=args.batch_size,
        test_frequency=args.test_frequency,
        test_batches=args.test_batches,
        eval_frequency=args.eval_frequency,
        eval_episodes=args.eval_episodes,
        initial_rtg=args.initial_rtg,
        prob_go_from_end=args.prob_go_from_end,
        eval_max_time_steps=args.eval_max_time_steps
    )

    if args.cuda:
        device = t.device("cuda" if t.cuda.is_available() else "cpu")
    else:
        device = t.device("cpu")

    if args.trajectory_path is None:
        raise ValueError("Must specify a trajectory path.")

    trajectory_data_set = TrajectoryLoader(
        args.trajectory_path, pct_traj=args.pct_traj, device=device)

    # make an environment 
    env_id = trajectory_data_set.metadata['args']['env_id']
    env = make_env(env_id, seed = 0, idx = 0, capture_video=False, run_name = "dev", fully_observed=False)
    env = env()

    if args.track:
        run_name = f"{env_id}__{args.exp_name}__{args.seed}__{int(time.time())}"
        wandb.init(
            project=args.wandb_project_name, 
            entity=args.wandb_entity, 
            name=run_name,
            config=args)

        fig = trajectory_data_set.plot_reward_over_time()
        wandb.log({"dataset/reward_over_time": wandb.Plotly(fig)})

    if args.linear_time_embedding:
        time_embedding_type = "linear"
    else:
        time_embedding_type = "embedding"

    # make a decision transformer
    dt = DecisionTransformer(
        env = env, 
        d_model = args.d_model,
        n_heads = args.n_heads,
        d_mlp = args.d_mlp,
        n_layers = args.n_layers,
        layer_norm = args.layer_norm,
        time_embedding_type = time_embedding_type,
        state_embedding_type="grid", # hard-coded for now to minigrid.
        max_timestep=trajectory_data_set.metadata.get("args").get("max_steps"), # so we can embed all the timesteps in the training data.
        n_ctx= args.n_ctx,
        device = device
    )

    if args.track:
        wandb.watch(dt, log="parameters")

    dt = train(
        dt = dt, 
        trajectory_data_set = trajectory_data_set, 
        env = env, 
        make_env=make_env,
        device=device, 
        batches=args.batches, 
        lr=args.learning_rate, 
        weight_decay=args.weight_decay,
        batch_size=args.batch_size, 
        track=args.track,
        test_frequency=args.test_frequency,
        test_batches = args.test_batches,
        eval_frequency=args.eval_frequency,
        eval_episodes=args.eval_episodes,
        initial_rtg=args.initial_rtg,
        prob_go_from_end=args.prob_go_from_end,
        eval_max_time_steps=args.eval_max_time_steps
    )

    if args.track:
        # save the model with pickle, then upload it as an artifact, then delete it.
        # name it after the run name.
        if not os.path.exists("models"):
            os.mkdir("models")

        model_path = f"models/{run_name}.pt"
        t.save(dt.state_dict(), model_path)
        artifact = wandb.Artifact(run_name, type="model")
        artifact.add_file(model_path)
        wandb.log_artifact(artifact)
        os.remove(model_path)

        wandb.finish()
