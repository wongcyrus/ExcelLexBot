# Install Code Formatter for Python and you need to set AWS Cloud9「Preferences」->「Python Support」->「Custom Code Formatter」
# yapf -i "$file"
sudo pip install yapf
sudo yum -y update
sudo yum -y install aws-cli
sudo -H pip install awscli --upgrade
# Install update SAM CLI to the latest version.
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install --update
rm -rf sam-installation
sam --version