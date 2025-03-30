from ipfs_dict_chain.IPFS import connect
from ipfs_dict_chain.IPFSDict import IPFSDict

# connect(host='127.0.0.1', port=5001)
data = IPFSDict(cid='Qmbu7h6JfTxHhv87QpFs9QahvuHorRVtwUriAzGakUeRP1')

print(data)