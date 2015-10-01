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
           This specifies the input format.
       -outform DER|PEM
           This specifies the output format
       -in <filename>
           This specifies the input filename to read a key from or standard
           input if this option is not specified.
       -passin <arg>
           the input file password source.
       -out <filename>
           This specifies the output filename to write a key to or standard
           output by is not specified.
       -passout <arg>
           the output file password source.
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
           by default a private key is output.
       -engine <id>
           specifying an engine (by its unique id string) will cause dsa to
           attempt to obtain a functional reference to the specified engine,
           thus initialising it if needed.


EXAMPLES
       To remove the pass phrase on a DSA private key:

           dsa -in key.pem -out keyout.pem

       To encrypt a private key using triple DES:

           dsa -in key.pem -des3 -out keyout.pem

       To convert a private key from PEM to DER format:

           dsa -in key.pem -outform DER -out keyout.der

       To print out the components of a private key to standard output:

           dsa -in key.pem -text -noout

       To just output the public part of a private key:

           dsa -in key.pem -pubout -out pubkey.pem
"""

from docpie import docpie, bashlog

if __name__ == '__main__':
    print(docpie(__doc__))
