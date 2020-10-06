
# RDS Setup

These scripts can help to setup a new RDS database with
postgis extensions and a SQL schema (based on a prior
RDS schema dump).  Some of this process might change if
the application tooling for db-schema migrations is
enabled and effective.

When the RDS is running in a private subnet of a VPC, the
process to connect and run the setup is something like:

1.  Create or start a t2.micro EC2 instance in the VPC,
    using a public subnet of the VPC.

2.  Get the PEM key required for secure access to the EC2
    - save the PEM key to `~/.aws/{stack-key-name}.pem`
    - create an entry in `~/.ssh/config` for connecting
      to the EC2 instance using the public IP address, e.g.

```text
Host appDevDbEC2
    HostName 34.221.219.62
    User ubuntu
    IdentityFile ~/.aws/app-key.pem

```

3.  Locate the default security group associated with
    the VPC:
    - CloudFormation -> Stack -> Resources -> VPC
    - get the VPC name and/or VPC-ID
    - Goto Security Groups and locate the default
      security group for this VPC
    - Edit inbound rules to add an 'ssh' port and
      select Custom -> My IP and save the changes

4.  Try to connect to the EC2 instance and rsync
    this directory to it:

```text
ssh -v appDevDbEC2
rsync -n -avz ./rds_setup appDevDbEC2:~/
```

5.  Get the admin user credentials and configure the
    `psql` environment variables in `.env`
    - use `.env_example` to create `.env`
    - as an option, setup a `~/.pgpass` file on the
      EC2 node with the admin user credentials and
      the RDS connection details (HOST, PORT).
    - the admin username and password should be saved
      in an AWS secret for the stack, see the
      `../rds_functions.sh` script for details.

6.  Run the setup commands in `setup.sh`
    - the execution might be commented out if was
      run already
    - update the pgdump file if a new schema is
      required

# RDS dumps

On an EC2 instance running an Ubuntu OS in the VPC of the RDS.  First
get the postgresql repository setup to install a specific client version
that matches the RDS postgresql version.
- https://wiki.postgresql.org/wiki/Apt

```shell script
sudo apt-get install curl ca-certificates gnupg
curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo apt-get update
sudo apt-get install postgresql-client-11
```

Then dump the RDS schema, e.g.

```shell script
./pg_dump_schema.sh
```
