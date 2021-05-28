[Unit]
Description=Jenkins Head Node
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=jenkins
ExecStart=docker run -v /home/jenkins/jenkins-homedir:/var/jenkins_home -p 8080:8080 ${docker_container}
[Install]
WantedBy=multi-user.target
