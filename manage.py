#!/usr/bin/python
import argparse
import os

import sys

project_path = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(project_path, "app")
python = os.path.join(project_path, "env/bin/python")
site_packages_path = os.path.join(project_path, "env/local/lib/python2.7/site-packages")

sys.path.append(app_path)
sys.path.append(site_packages_path)

from app import (
    configs,
    model
)


def init_db(ec):
    import sqlalchemy
    engine = sqlalchemy.create_engine(ec.db_uri)
    model.Base.metadata.create_all(engine)


def gunicorn(ec):
    cmd = [
        "%s/env/bin/gunicorn" % project_path,
        "--chdir",
        app_path,
        "api:app",
        "--worker-class",
        ec.gunicorn_worker_type,
        "-b",
        "0.0.0.0:5000",
        "--log-level",
        ec.logging_level.lower(),
        "-w",
        "%s" % ec.gunicorn_workers,
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.gunicorn_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execve(cmd[0], cmd, os.environ)


def matchbox(ec):
    cmd = [
        "%s/runtime/matchbox/matchbox" % project_path,
        "-address",
        ec.matchbox_uri.replace("https://", "").replace("http://", ""),
        "-assets-path",
        "%s" % ec.matchbox_assets,
        "-data-path",
        "%s" % ec.matchbox_path,
        "-log-level",
        ec.logging_level.lower(),
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.matchbox_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execve(cmd[0], cmd, os.environ)


def plan(ec):
    cmd = [
        python,
        "%s/plans/k8s_2t.py" % app_path,
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    with open(ec.plan_pid_file, "w") as f:
        f.write("%d" % os.getpid())
    os.execve(cmd[0], cmd, os.environ)


def validate():
    cmd = [
        python,
        "%s/validate.py" % project_path,
    ]
    os.write(1, "PID  -> %s\n"
                "exec -> %s\n" % (os.getpid(), " ".join(cmd)))
    os.execve(cmd[0], cmd, os.environ)


def show_configs(ec):
    for k, v in ec.__dict__.iteritems():
        print "%s=%s" % (k, v)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Enjoliver')
    parser.add_argument('task', type=str, choices=["gunicorn", "plan", "matchbox", "show-configs", "validate"],
                        help="Choose the task to run")
    parser.add_argument('--configs', type=str, default="%s/configs.yaml" % app_path,
                        help="Choose the yaml config file")
    task = parser.parse_args().task
    f = parser.parse_args().configs
    ec = configs.EnjoliverConfig(f)
    if task == "gunicorn":
        init_db(ec)
        gunicorn(ec)
    elif task == "plan":
        plan(ec)
    elif task == "matchbox":
        matchbox(ec)
    elif task == "show-configs":
        show_configs(ec)
    elif task == "validate":
        validate()
    else:
        raise AttributeError("%s not a choice" % task)