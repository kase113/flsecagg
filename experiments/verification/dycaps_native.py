#!/usr/bin/env python3
"""Verify the unchanged DyCAPS binary and TCP handoff test in isolated runs."""

import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream/dycaps"
OUTPUT = ROOT / "results/upstream-verification/dycaps"


def command(arguments, directory, log, timeout=120, check=True):
    with (OUTPUT / log).open("w") as stream:
        result = subprocess.run(arguments, cwd=directory, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"command failed; see {OUTPUT / log}")
    return result.returncode


def free_ports(count):
    sockets = []
    try:
        for _ in range(count):
            listener = socket.socket()
            listener.bind(("127.0.0.1", 0))
            sockets.append(listener)
        return [listener.getsockname()[1] for listener in sockets]
    finally:
        for listener in sockets:
            listener.close()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "result.json").unlink(missing_ok=True)
    result = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=UPSTREAM, text=True).strip(),
        "go": subprocess.check_output(["go", "version"], text=True).strip(),
    }
    with tempfile.TemporaryDirectory(prefix="dycaps-native-") as temporary:
        temporary = Path(temporary)
        binary = temporary / "dycaps"
        command(["go", "build", "-o", str(binary), "./cmd/DyCAPs"], UPSTREAM, "build.log")
        command([str(binary), "-n", "4", "-f", "1", "-op1", "1"], temporary, "setup.log")
        for role in ("currentCommitee", "newCommitee"):
            code = command([str(binary), "-n", "4", "-f", "1", "-op2", role], temporary, f"invalid-{role}.log", timeout=5)
            assert code == 0
        result["unrecognized_launcher_roles_exit_zero"] = True
        lists = temporary / "list"
        lists.mkdir()
        ports = free_ports(8)
        for suffix, values in (("", ports[:4]), ("Next", ports[4:])):
            (lists / f"ipList{suffix}").write_text("127.0.0.1\n" * 4)
            (lists / f"portList{suffix}").write_text("\n".join(map(str, values)) + "\n")
        metadata = OUTPUT / "native-metadata"
        metadata.mkdir(exist_ok=True)
        for old_log in metadata.iterdir():
            if old_log.is_file():
                old_log.unlink()
        processes = []
        streams = []
        started = time.monotonic()
        try:
            roles = [("newCommittee", index) for index in range(4)]
            roles += [("oldCommittee", index) for index in range(4)] + [("client", 0)]
            for role, index in roles:
                stream = (OUTPUT / f"native-{role}-{index}.log").open("w")
                streams.append(stream)
                processes.append(subprocess.Popen([
                    str(binary), "-n", "4", "-f", "1", "-op2", role, "-id", str(index),
                    "-mp", str(metadata), "-lp", str(lists), "-t1", "2", "-t2", "3", "-t3", "4",
                ], cwd=temporary, stdout=stream, stderr=subprocess.STDOUT))
            while time.monotonic() - started < 30:
                if any(process.poll() is not None for process in processes):
                    raise RuntimeError("native process exited before handoff completed")
                complete = [metadata / f"lognew{index}" for index in range(4)]
                if all(path.exists() and "ShareDistLatency," in path.read_text() for path in complete):
                    break
                time.sleep(0.1)
            else:
                raise TimeoutError("native handoff did not complete in 30 seconds")
            result["native_tcp_handoff_members"] = 4
            result["native_wall_seconds_including_startup"] = time.monotonic() - started
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for stream in streams:
                stream.close()
        print("PASS: unchanged binary, four new TCP members complete handoff", flush=True)

        source = UPSTREAM / "internal/party/Complete_test.go"
        relocated = temporary / "Complete_test.go"
        ports = free_ports(26)
        source_text = source.read_text()
        for original, replacement in zip(range(8880, 8906), ports):
            source_text = source_text.replace(f'"{original}"', f'"{replacement}"')
        relocated.write_text(source_text)
        overlay = temporary / "overlay.json"
        overlay.write_text(json.dumps({"Replace": {str(source): str(relocated)}}))
        command([
            "go", "test", "-overlay", str(overlay), "-count=1", "-v", "-timeout=45s",
            "-run", "^TestCompleteProcess$", "./internal/party",
        ], UPSTREAM, "complete-process.log", timeout=60)
        transcript = (OUTPUT / "complete-process.log").read_text()
        recovered = re.findall(r"Recovered secret from new (?:reducedShares|fullShares):\s*(\d+)", transcript)
        assert recovered == ["1111111111111112345"] * 2, recovered
        result["native_tcp_test_members"] = 10
        result["reduced_and_full_share_reconstruction"] = "match original secret"
        print("PASS: upstream ten-member TCP test reconstructs original secret twice", flush=True)
    (OUTPUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
