# Parameters -----------------------------------------------

'''
num_conv
conv_size
conv_channels
conv_extend_mode
num_fc
fc_sizes
'''

# Test 1 ---------------------------------------------------

cnn_1 = "C(5,5,1):R:P(5,5):C(5,3,1):R:P(2,2):F(100):R:BN1:F(100):R:BN1:F(100):R:BN1:F(2):S",

EXTEND = ('const', 'decay')
MODES = ('se', 'bw', 'mb')

def gen_cnn(bn_at_f=True, bn_at_c=False, cv_num=3, cv_size=5, cv_channels=5, cv_mode='decay', cv_decay=5/3, fc_num=3, fc_size=100, fc_mode='const', mode='bw', inputs=1):
    definition = []
    for i in range(cv_num):
        definition.append(f"C()")
