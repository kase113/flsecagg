import argparse
import contextlib
import json
import pathlib
import signal
import socket
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--n", type=int, default=4)
    parser.add_argument("--f", type=int, default=1)
    parser.add_argument("--seconds", type=int, default=20)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    binary = str(args.binary.resolve())
    ports = list(range(8880, 8880 + args.n)) + list(range(8890, 8890 + args.n))
    with contextlib.ExitStack() as stack:
        for port in ports:
            listener = stack.enter_context(socket.socket())
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("0.0.0.0", port))
    (output / "listeners-before.log").write_text(subprocess.check_output(["ss", "-ltnp"], text=True))
    for suffix, base in [("", 8880), ("Next", 8890)]:
        (output / ("ipList" + suffix)).write_text("127.0.0.1\n" * args.n)
        (output / ("portList" + suffix)).write_text("".join(f"{base + node}\n" for node in range(args.n)))
    common = [binary, "-n", str(args.n), "-f", str(args.f)]
    with (output / "setup.log").open("w") as stream:
        subprocess.run(common + ["-op1", "1"], cwd=output, stdout=stream, stderr=subprocess.STDOUT, check=True)
    processes = []
    completed = False
    started = time.monotonic()
    try:
        with contextlib.ExitStack() as stack:
            for role in ["old", "new"]:
                for node in range(args.n):
                    command = common + ["-op1", "2", "-op2", role, "-id", str(node), "-mp", str(output), "-lp", str(output), "-t1", "2", "-t2", "3"]
                    stream = stack.enter_context((output / f"{role}-{node}.stdout.log").open("w"))
                    process = subprocess.Popen(command, cwd=output, stdout=stream, stderr=subprocess.STDOUT)
                    processes.append(process)
                    print(json.dumps({"pid": process.pid, "command": command}), flush=True)
            while time.monotonic() - started < args.seconds:
                completed = all(
                    (output / f"exeLog{role}{node}.log").exists()
                    and f"Dpss{role} finished" in (output / f"exeLog{role}{node}.log").read_text()
                    for role in ["Old", "New"] for node in range(args.n)
                )
                if completed or any(process.poll() is not None for process in processes):
                    break
                time.sleep(0.1)
            if not completed:
                for process in processes:
                    if process.poll() is None:
                        process.send_signal(signal.SIGQUIT)
            print(json.dumps({"all_protocols_finished": completed, "elapsed_seconds": time.monotonic() - started}), flush=True)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        (output / "process-exits.json").write_text(json.dumps({process.pid: process.returncode for process in processes}))
    return 0 if completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
