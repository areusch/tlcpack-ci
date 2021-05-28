[Unit]
Description=Jenkins Head Node
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=jenkins
ExecStart=docker run -v /home/jenkins/jenkins-homedir:/var/jenkins_home -p 8080:8080 {{ jenkins_master_container_tag }}
[Install]
WantedBy=multi-user.target
