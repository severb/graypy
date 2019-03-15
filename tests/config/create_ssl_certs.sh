#!/bin/bash -e

#
# This scrip generate self-signed certificate to be used in development.
# it sets the CN to the first provided hostname and will add all other
# provided names to subjectAltName.
#
# Some Magic is added to the script that tries to find some settings for the
# current host where this script is started.
#
# This script was first created by Jan Doberstein <jd@jalogis.ch> 2017-07-30
#
# This script is tested on CentOS 7, Ubuntu 14.04, Ubuntu 16.04, MacOS 10.12

OPSSLBIN=$(which openssl)

while getopts "d:h:i:m?" opt; do
  case ${opt} in
    h) HNAME+=("${OPTARG}");;
    i) HIP+=("${OPTARG}");;
    m) MMODE=active;;
    d) VALIDDAYS=${OPTARG};;
    s) KEYSECRET=${OPTARG};;
    ?) HELPME=yes;;
    *) HELPME=yes;;
  esac
done

if [ -n "${HELPME}" ]; then
  echo "
  This script will generate self-signed ssl certificates, they will be written to the current directory
  Options available:
      -h  to set Hostnames (can be used multiple times)
      -i  to set IP Adresses (can be used multiple times)
      -m  (optional) activates a magic mode where the script try to find Hostnames and IPs of the current Host
      -d  (optional) Number of Days the certificate is valid (default=365)
      -s  (optional) The secret that is used for the crypted key (default=secret)
  "
  exit 0

fi

if [ -n "${MMODE}" ]; then
  echo "Magic Mode is on
   this will try to find the hostname and IP of host where this script is executed.
   it will then add this to the list of possible Hostnames and IPs

   If you get an error with the Magic Mode then retry with only one hostname set via -h option

  "

  HOSTNAME_BIN=$(type -p hostname)

  # possible addition
  #
  # try if dig is installed and check the hostname and ip resolve
  # dig_bin=$(which dig)

  if [ -n "${HOSTNAME_BIN}" ];then
    HNAME+=("$(hostname -s)")
    HNAME+=("$(hostname -A)")
    # add localhost as hostname to easy up debugging
    HNAME+=(localhost)
    # try if hostname -I returns the IP, if not
    # nasty workaround two steps because the array will get
    # entries that can't be parsed out correct
    GETIP=$({hostname -I 2>/dev/null || echo "127.0.0.1")
    HIP+=($(echo $GETIP | tr -d '[:blank:]'))
  else
    echo "The command hostname can't be found
    aborting Magic mode
    please use manual mode and provide at least one hostname with -h
    "
    exit 1
  fi

  # take all IP Adresses returned by the command IP into the list
  # first check if all binaries are present that are needed
  # (when only bash build-ins are needed would be awesome)
  IPCMD=$(type -p ip)
  GRPCMD=$(type -p grep)
  AWKCMD=$(type -p  awk)
  CUTCMD=$(type -p cut)

  if [ -n "${IPCMD}" ] && [ -n "${GRPCMD}" ] && [ -n "${AWKCMD}" ] && [ -n "${CUTCMD}" ]; then
    # to avoid error output in the array 2>/dev/null
    # every IP that is returned will be added to the array
    # ip addr show | grep 'inet ' | awk '{ print $2}' | cut -d"/" -f1
    HIP+=($("${IPCMD}" addr show 2>/dev/null | "${GRPCMD}" 'inet ' 2>/dev/null| "${AWKCMD}" '{print $2}' 2>/dev/null| "${CUTCMD}" -d"/" -f1 2>/dev/null))
  fi
fi

if [ -z "${HNAME}" ]; then
  echo "please provide hostname (-h) at least once. Try -? for help.";
  exit 1;
fi

if [ -z "${OPSSLBIN}" ]; then
  echo "no openssl detected aborting"
  exit 1;
fi

# set localhost IP if no other set
if [ -z "${HIP}" ]; then
  HIP+=(127.0.0.1)
fi

# if no VALIDDAYS are set, default 365
if [ -z "${VALIDDAYS}" ]; then
  VALIDDAYS=365
fi

# if no Key provided, set default secret
if [ -z "${KEYSECRET}" ]; then
  KEYSECRET=secret
fi


# sort array entries and make them uniq
NAMES=($(printf "DNS:%q\n" ${HNAME[@]} | sort -u))
IPADD=($(printf "IP:%q\n" ${HIP[@]} | sort -u))

# print each elemet of both arrays with comma seperator
# and create a string from the array content
SUBALT=$(IFS=','; echo "${NAMES[*]},${IPADD[*]}")

#### output some informatione
echo "This script will generate a SSL certificate with the following settings:
CN Hostname = ${HNAME}
subjectAltName = ${SUBALT}
"
# ---------------------------

local_openssl_config="
[ req ]
prompt = no
distinguished_name = req_distinguished_name
x509_extensions = san_self_signed
[ req_distinguished_name ]
CN=${HNAME}
[ san_self_signed ]
subjectAltName = ${SUBALT}
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = CA:true
"

 ${OPSSLBIN} req \
  -newkey rsa:2048 -nodes \
  -keyout "${HNAME}.pkcs5-plain.key.pem" \
  -x509 -sha256 -days ${VALIDDAYS} \
  -config <(echo "$local_openssl_config") \
  -out "${HNAME}.cert.pem" 2>openssl_error.log || { echo -e "ERROR !\nOpenSSL returns an error, sorry this script will not work \n Possible reason: the openssl version is to old and does not support self signed san certificates \n Check openssl_error.log in your current directory for details"; exit 1; }

${OPSSLBIN} pkcs8 -in "${HNAME}.pkcs5-plain.key.pem" -topk8 -nocrypt -out "${HNAME}.pkcs8-plain.key.pem"
${OPSSLBIN} pkcs8 -in "${HNAME}.pkcs5-plain.key.pem" -topk8 -passout pass:"${KEYSECRET}" -out "${HNAME}.pkcs8-encrypted.key.pem"

echo "the following files are written to the current directory:"
echo "  - ${HNAME}.pkcs5-plain.key.pem"
echo "  - ${HNAME}.pkcs8-plain.key.pem"
echo "  - ${HNAME}.pkcs8-encrypted.key.pem"
echo "    with the password: ${KEYSECRET}"
echo ""

rm openssl_error.log

#EOF
