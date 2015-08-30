"""
NAME
       dsa - DSA key processing

USAGE:
       dsa [-inform (PEM|DER)] [-outform (PEM|DER)] [-in <filename>]
           [-passin <arg>] [-out <filename>] [-passout <arg>] [-aes128] [-aes192]
           [-aes256] [-camellia128] [-camellia192] [-camellia256] [-des] [-des3]
           [-idea] [-text] [-noout] [-modulus] [-pubin] [-pubout] [-engine <id>]

OPTIONS:
       -inform DER|PEM
           This specifies the input format. The DER option with a private key
           uses an ASN1 DER encoded form of an ASN.1 SEQUENCE consisting of
           the values of version (currently zero), p, q, g, the public and
           private key components respectively as ASN.1 INTEGERs. When used
           with a public key it uses a SubjectPublicKeyInfo structure: it is
           an error if the key is not DSA.

           The PEM form is the default format: it consists of the DER format
           base64 encoded with additional header and footer lines. In the case
           of a private key PKCS#8 format is also accepted.
       -outform DER|PEM
           This specifies the output format, the options have the same meaning
           as the -inform option.
       -in <filename>
           This specifies the input filename to read a key from or standard
           input if this option is not specified. If the key is encrypted a
           pass phrase will be prompted for.
       -passin <arg>
           the input file password source. For more information about the
           format of arg see the PASS PHRASE ARGUMENTS section in openssl(1).
       -out <filename>
           This specifies the output filename to write a key to or standard
           output by is not specified. If any encryption options are set then
           a pass phrase will be prompted for. The output filename should not
           be the same as the input filename.
       -passout <arg>
           the output file password source. For more information about the
           format of arg see the PASS PHRASE ARGUMENTS section in openssl(1).
       -text
           prints out the public, private key components and parameters.
       -noout
           this option prevents output of the encoded version of the key.
       -modulus
           this option prints out the value of the public key component of the
           key.
       -pubin
           by default a private key is read from the input file: with this
           option a public key is read instead.
       -pubout
           by default a private key is output. With this option a public key
           will be output instead. This option is automatically set if the
           input is a public key.
       -engine <id>
           specifying an engine (by its unique id string) will cause dsa to
           attempt to obtain a functional reference to the specified engine,
           thus initialising it if needed. The engine will then be set as the
           default for all available algorithms.

NOTES
       The PEM private key format uses the header and footer lines:

        -----BEGIN DSA PRIVATE KEY-----
        -----END DSA PRIVATE KEY-----

       The PEM public key format uses the header and footer lines:

        -----BEGIN PUBLIC KEY-----
        -----END PUBLIC KEY-----

EXAMPLES
       To remove the pass phrase on a DSA private key:

        openssl dsa -in key.pem -out keyout.pem

       To encrypt a private key using triple DES:

        openssl dsa -in key.pem -des3 -out keyout.pem

       To convert a private key from PEM to DER format:

        openssl dsa -in key.pem -outform DER -out keyout.der

       To print out the components of a private key to standard output:

        openssl dsa -in key.pem -text -noout

       To just output the public part of a private key:

        openssl dsa -in key.pem -pubout -out pubkey.pem
"""

from docpie import docpie, bashlog

bashlog.stdoutlogger(None, bashlog.DEBUG)

print(docpie(__doc__, stdopt=False))
