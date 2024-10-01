##############################################################################
# Copyright (c) 2017,  Met Office, on behalf of HMSO and Queen's Printer
# For further details please refer to the file LICENCE.original which you
# should have received as part of this distribution.
##############################################################################


'''
PSyclone transformation script for a generic transformation of 

'''


def trans(file_container):
    '''Just adds a comment to the file to show that the file was processed.

    '''
    file_container.append_preceding_comment("Processed by umscript.py")
    file_container.append_preceding_comment("------------------------")
    file_container.append_preceding_comment("")
    # Obviously, you can do any other transformation here.
