FROM centos
LABEL org.privatecontainers.image.authors="centerupt@gmail.com"

ARG MYUSER
ENV USER=$MYUSER
ENV HOME=/home/$MYUSER

RUN dnf --disablerepo '*' --enablerepo=extras swap centos-linux-repos centos-stream-repos -y # buildkit
RUN yum -y update # buildkit
RUN yum install man git gcc openssl-devel bzip2-devel libffi-devel zlib-devel zlib-devel sqlite-devel wget vim sudo net-tools yum-utils vim sudo net-tools passwd ncurses ncurses-term ncurses-devel ncurses-compat-libs ncurses-c++-libs ncurses-libs -y # buildkit
RUN curl https://www.python.org/ftp/python/3.9.15/Python-3.9.15.tgz --output /tmp/Python-3.9.15.tgz # buildkit
WORKDIR /tmp
RUN tar xzf Python-3.9.15.tgz # buildkit
WORKDIR /tmp/Python-3.9.15
RUN ./configure --enable-optimizations # buildkit
RUN yum install make -y # buildkit
RUN make altinstall # buildkit
RUN yum install sudo which -y # buildkit
WORKDIR /tmp
RUN rm -r Python-3.9.15.tgz # buildkit
RUN yum -y install epel-release coreutils python3-argcomplete --allowerasing # buildkit
RUN curl https://bootstrap.pypa.io/get-pip.py --output get-pip.py # buildkit
RUN python3.9 get-pip.py # buildkit
RUN python3.9 -m pip install --upgrade pip # buildkit
WORKDIR /var/tmp
COPY . /var/tmp/

# packages required after installing epel-release
RUN yum -y install openssh-server openssh-clients sudo pinentry # buildkit

# mount secrets and add our default user; this is used in the container as your SSO_USER
RUN --mount=type=secret,id=my_env source /run/secrets/my_env && adduser -m $USER --shell /bin/bash --comment "goat user" &&\
     usermod -aG wheel $USER &&\
     mkdir -p /home/$USER/.ssh &&\
     mkdir -p /home/$USER/.gnupg &&\
     chown $USER:$USER -R /home/$USER/ &&\
     chmod 700 /home/$USER/.ssh &&\
     echo "$USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers &&\
     echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers &&\
     echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config &&\
     ssh-keyscan github.com > /home/$USER/.ssh/known_hosts

# Add the keys and set permissions on files of interest
RUN --mount=type=secret,id=my_env source /run/secrets/my_env && echo "$SSH_PRV_KEY" > /home/$USER/.ssh/id_rsa && \
    echo "$SSH_PUB_KEY" > /home/$USER/.ssh/id_rsa.pub && \
    chmod 600 /home/$USER/.ssh/id_rsa && \
    mkdir /home/${USER}/git && \
    chmod 755 /home/${USER}/git && \
    chown $USER:$USER /home/${USER}/git && \
    chown $USER:$USER /home/$USER/.ssh/id_rsa && \
    chown $USER:$USER /home/$USER/.ssh/id_rsa.pub && \
    chown $USER:$USER /home/$USER/.ssh/known_hosts && \
    chmod 600 /home/$USER/.ssh/id_rsa.pub && \
    touch /home/$USER/.flyrc && \
    chown $USER:$USER /home/$USER/.flyrc

# install additional packages
RUN yum -y install python3-boto3 jq awscli gnupg2 npm python3-tabulate # buildkit
RUN systemctl enable sshd.service # buildkit

# first setup our new python
RUN unlink /usr/bin/python3
RUN ln -s /usr/local/bin/python3.9 /usr/bin/python3

# prepare gpg to generate keys automatically later
RUN --mount=type=secret,id=my_env source /run/secrets/my_env && touch /home/$USER/.gnupg/gpg-agent.conf &&\
     chmod 700 -R /home/$USER/.gnupg &&\
     chown -R $USER:$USER /home/$USER &&\
     chown -R ${USER}:${USER} /home/${USER}/.gnupg &&\
     echo 'pinentry-program /usr/bin/pinentry-curses' > /home/$USER/.gnupg/gpg-agent.conf &&\
     gpg-agent --daemon --options /home/$USER/.gnupg/gpg-agent.conf # buildkit

RUN cp /var/tmp/load_prompt.sh /home/${USER}/
RUN cp /var/tmp/.bashrc /home/${USER}/
RUN cp /var/tmp/.bash_profile /home/${USER}/
RUN chown ${USER}:${USER} /home/${USER}/.bashrc
RUN chown ${USER}:${USER} /home/${USER}/.bash_profile
RUN chown ${USER}:${USER} /home/${USER}/load_prompt.sh
RUN chmod 777 /usr/share/man/man1

RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - $USER -c "git config --global user.email ${USER}@localhost.com"
RUN --mount=type=secret,id=my_env source /run/secrets/my_env && sudo su - $USER -c "git config --global user.name ${USER}"

USER "$USER"
RUN python3.9 -m pip install --upgrade pip # buildkit
RUN sudo activate-global-python-argcomplete # buildkit
RUN pip install goatshell

# now install man pages for goat
RUN sudo chmod 755 /usr/share/man/man1
# our working directory will be HOME
WORKDIR $HOME
