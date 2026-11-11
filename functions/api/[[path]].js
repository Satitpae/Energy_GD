import {handleApi} from '../../cloud/api.mjs';
export const onRequest=({request,env})=>handleApi(request,env);
