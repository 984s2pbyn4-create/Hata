/* ATELIER / STANDALONE GLB VIEWER
   Intentionally uses no CDN, third-party JS, WebGL frameworks or paid APIs.
   Every mode uses meshes contained in the exported GLB files; no changes to the shell.
   GLB support is intentionally scoped to our generated, untextured, vertex-colour triangle meshes.
*/
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const STYLE_NAMES={warm:'Графит + орех',japandi:'Оливковый Tech',graphite:'Ночной графит'};
const viewPresets={
 whole:{az:-.36,el:.70,dist:16.6,target:[5.58,-.35,5.72]},
 top:{az:0,el:1.565,dist:18.1,target:[5.58,0,5.72]},
 kitchen:{az:-.48,el:.86,dist:8.3,target:[4.12,.35,5.99]},
 living:{az:-.46,el:.75,dist:8.2,target:[3.97,.30,9.54]},
 bedroom:{az:.30,el:.85,dist:7.6,target:[5.96,.35,2.27]},
 bath:{az:.43,el:.86,dist:5.8,target:[8.65,.25,6.03]},
 hall:{az:-.20,el:.92,dist:7.4,target:[7.07,.35,7.48]},
 closet:{az:-.9,el:.97,dist:4.4,target:[6.85,.55,10.56]},
 balcony:{az:-.40,el:.84,dist:4.5,target:[2.77,.35,3.45]},
 walkKitchen:{az:-2.44,el:.16,dist:3.02,target:[4.19,1.06,7.38]},
 walkLiving:{az:-.38,el:.14,dist:2.72,target:[4.1,1.20,8.35]},
 walkBedroom:{az:-.46,el:.19,dist:2.29,target:[5.90,1.11,1.61]}
};
const roomGallery=['overall','kitchen','living','bedroom','bath'];
const eyeGallery=['kitchen_a','kitchen_b','living_a','living_b','bedroom_a','bedroom_b','bath_a'];
const eyeNames={kitchen_a:'Кухня · ракурс A',kitchen_b:'Кухня · ракурс Б',living_a:'Гостиная · ракурс A',living_b:'Гостиная · ракурс Б',bedroom_a:'Спальня · ракурс A',bedroom_b:'Спальня · ракурс Б',bath_a:'Ванная · внутри'};
const ROOM_INFO={whole:['Вся квартира','Два входа в гардеробную','Персональная схема для семьи с двумя детьми'],top:['Вид сверху','Планировка','Существующие двери в гардеробную: спальня + коридор'],kitchen:['Кухня-гостиная','15,4 м²','Кинотеатр, диван-кровать, стол на шесть'],living:['Спальня родителей','13,8 м²','Кровать 180×200, ТВ, кроватка, туалетный столик'],bedroom:['Детская','12,2 м²','Сейчас игры, затем рабочие места и спальные зоны'],bath:['Санузлы','≈3,5 м² + туалет','Ванна, стиральная машина и кошачий лоток'],hall:['Коридор','7,8 м²','Два входа в гардеробную: из спальни и коридора'],closet:['Гардеробная','≈1,8 м²','Вход из коридора и из родительской спальни'],balcony:['Лоджия','≈3,4 м²','FDM и гидропоника условно; смоляной принтер не размещён']};
const DESIGN_SPEC={warm:['DARK TECH · тёплая версия','Графит · тёмный орех · мягкий песочный текстиль','Детская светлее, скрываемый рабочий стол, многоуровневый свет'],japandi:['DARK TECH · оливковая версия','Графит · шалфей · древесина · тёплые ткани','Биофильные акценты при единой технологичной композиции'],graphite:['DARK TECH · контрастная версия','Ночной графит · металл · тёмная древесина','Максимальная контрастность, тёплые линейные акценты']};
const galleryNames={overall:'Вся квартира',kitchen:'Кухня',living:'Гостиная',bedroom:'Спальня',bath:'Санузел'};
const ui={style:'warm',secondStyle:'japandi',mode:'interior',compare:false,cut:true,light:'day',brightness:1,view:'whole',stage:'now',scenario:'daily',mechanisms:{peninsula:0,laptop:0,screen:0,wardrobe:0},cinema:false};
const camera={...viewPresets.whole,target:[...viewPresets.whole.target]};
const models=new Map();
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{const n=Math.hypot(...a)||1;return a.map(x=>x/n);};
const mat4mul=(a,b)=>{const o=new Float32Array(16);for(let j=0;j<4;j++)for(let i=0;i<4;i++)for(let k=0;k<4;k++)o[j*4+i]+=a[k*4+i]*b[j*4+k];return o;};
function lookAt(eye,center,up=[0,1,0]){
 const z=norm(sub(eye,center)),x=norm(cross(up,z)),y=cross(z,x);
 return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]);
}
function perspective(fov,aspect,near,far){const f=1/Math.tan(fov/2),v=1/(near-far);return new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)*v,-1,0,0,2*far*near*v,0]);}
function ortho(l,r,b,t,n,f){return new Float32Array([2/(r-l),0,0,0,0,2/(t-b),0,0,0,0,-2/(f-n),0,-(r+l)/(r-l),-(t+b)/(t-b),-(f+n)/(f-n),1]);}
function cameraVP(aspect){const {az,el,target}=camera;const dist=camera.dist*Math.max(ui.compare?1.7:1,1.02/aspect);const v=[dist*Math.cos(el)*Math.sin(az),dist*Math.sin(el),dist*Math.cos(el)*Math.cos(az)];const eye=target.map((x,i)=>x+v[i]);return mat4mul(perspective(42*Math.PI/180,aspect,.05,100),lookAt(eye,target));}
function lightVP(){const look=[5.5,0,5.8],eye=[-3,17,12];return mat4mul(ortho(-11,11,-12,12,1,45),lookAt(eye,look));}
function decodeAccessor(gltf,bin,accessorId){
 const a=gltf.accessors[accessorId],bv=gltf.bufferViews[a.bufferView];const n={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];if(!n)throw Error('Unsupported accessor '+a.type);
 const sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};const bytes=sizes[a.componentType];if(!bytes)throw Error('Unsupported type '+a.componentType);
 const stride=bv.byteStride||bytes*n,base=bin.byteOffset+(bv.byteOffset||0)+(a.byteOffset||0),view=new DataView(bin.buffer);
 const result=new Float32Array(a.count*n);
 for(let i=0;i<a.count;i++)for(let j=0;j<n;j++){
  const off=base+i*stride+j*bytes;let v;
  switch(a.componentType){case 5120:v=view.getInt8(off);break;case 5121:v=view.getUint8(off);break;case 5122:v=view.getInt16(off,true);break;case 5123:v=view.getUint16(off,true);break;case 5125:v=view.getUint32(off,true);break;default:v=view.getFloat32(off,true);}
  if(a.normalized){if(a.componentType===5121)v/=255;else if(a.componentType===5123)v/=65535;else if(a.componentType===5120)v=Math.max(-1,v/127);else if(a.componentType===5122)v=Math.max(-1,v/32767);}
  result[i*n+j]=v;
 }
 return {data:result,n};
}
function transformPoint(pos,m){if(!m)return pos;return [m[0]*pos[0]+m[4]*pos[1]+m[8]*pos[2]+m[12],m[1]*pos[0]+m[5]*pos[1]+m[9]*pos[2]+m[13],m[2]*pos[0]+m[6]*pos[1]+m[10]*pos[2]+m[14]];}
function quaternionMatrix(q){const [x,y,z,w]=q;return new Float32Array([1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w),0,2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w),0,2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y),0,0,0,0,1]);}
function nodeTransform(n,parent){const id=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);let m=n.matrix?new Float32Array(n.matrix):id;
 if(!n.matrix){if(n.rotation)m=mat4mul(m,quaternionMatrix(n.rotation));if(n.scale){for(let j=0;j<3;j++)for(let i=0;i<4;i++)m[4*j+i]*=n.scale[j];}if(n.translation){m[12]=n.translation[0];m[13]=n.translation[1];m[14]=n.translation[2];}}
 return mat4mul(parent,m);
}
async function loadModel(name){
 const cacheKey=name==='shell'?'shell':`${name}-${ui.stage}-${ui.scenario}`;if(models.has(cacheKey))return models.get(cacheKey);
 const task=(async()=>{
  const path=name==='shell'?'models/kvartira-planirovka.glb':`models/kvartira-${name}-${ui.stage}-${ui.scenario}.glb`;
  const response=await fetch('./'+path);if(!response.ok)throw Error('Не удалось открыть '+path+' (HTTP '+response.status+')');
  const raw=await response.arrayBuffer(),v=new DataView(raw);if(v.getUint32(0,true)!==0x46546c67)throw Error('GLB header');
  const jsonLength=v.getUint32(12,true),jsonType=v.getUint32(16,true);if(jsonType!==0x4e4f534a)throw Error('GLB JSON chunk');
  const gltf=JSON.parse(new TextDecoder().decode(new Uint8Array(raw,20,jsonLength)));
  const binPos=20+jsonLength,binLength=v.getUint32(binPos,true),binType=v.getUint32(binPos+4,true);if(binType!==0x004e4942)throw Error('GLB BIN chunk');
  const bin=new Uint8Array(raw,binPos+8,binLength);const V=[],N=[],C=[],W=[],M=[],F=[];let triangles=0,wallTris=0;
  const materialCode=name=>{
   if(/^wall_/.test(name))return 7;
   if(/^floor_(kitchen|bedroom|living)$/.test(name))return 1;
   if(/^floor_(bath|wc|hall|closet|balcony)$/.test(name))return 8;
   if(/custom_(wood|woodDark|floorLine)_/.test(name))return 1;
   if(/custom_(marble|stone)_/.test(name))return 2;
   if(/custom_(fabric|rug|accent)_/.test(name))return 3;
   if(/custom_(metal|glass)_/.test(name))return 5;
   if(/custom_green_/.test(name))return 6;
   if(/custom_tile_/.test(name))return 8;
   return 0;
  };
  function walk(nodeId,parent){const n=gltf.nodes[nodeId],xf=nodeTransform(n,parent),isWall=/^wall_/.test(n.name||''),mat=materialCode(n.name||'');const feature=/feature_peninsula/.test(n.name||'')?1:/feature_laptop/.test(n.name||'')?2:/feature_screen/.test(n.name||'')?3:/feature_wardrobe/.test(n.name||'')?4:0;
   if(n.mesh!==undefined){for(const primitive of gltf.meshes[n.mesh].primitives){if((primitive.mode??4)!==4)continue;
    const positions=decodeAccessor(gltf,bin,primitive.attributes.POSITION),colors=primitive.attributes.COLOR_0!==undefined?decodeAccessor(gltf,bin,primitive.attributes.COLOR_0):null;
    const indices=primitive.indices!==undefined?decodeAccessor(gltf,bin,primitive.indices).data:null;
    const ct=indices?indices.length:positions.data.length/3;
    for(let k=0;k+2<ct;k+=3){const points=[],cols=[];
     for(let j=0;j<3;j++){
      const ii=indices?indices[k+j]:k+j, p=[positions.data[ii*3],positions.data[ii*3+1],positions.data[ii*3+2]];
      points.push(transformPoint(p,xf));cols.push(colors?[colors.data[ii*colors.n],colors.data[ii*colors.n+1],colors.data[ii*colors.n+2]]:[.82,.8,.76]);
     }
     const normal=norm(cross(sub(points[1],points[0]),sub(points[2],points[0])));
     for(let j=0;j<3;j++){V.push(...points[j]);N.push(...normal);C.push(...cols[j]);W.push(isWall?1:0);M.push(mat);F.push(feature);}
     triangles++;if(isWall)wallTris++;
    }
   }}
   for(const child of n.children||[])walk(child,xf);
  }
  const identity=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
  for(const root of gltf.scenes[gltf.scene||0].nodes)walk(root,identity);
  // Interleaved: position(3), normal(3), color(3), wall(1), material(1), moveable feature(1).
  const packed=new Float32Array(triangles*3*12);
  for(let j=0;j<triangles*3;j++){const i=j*12;packed.set(V.slice(j*3,j*3+3),i);packed.set(N.slice(j*3,j*3+3),i+3);packed.set(C.slice(j*3,j*3+3),i+6);packed[i+9]=W[j];packed[i+10]=M[j];packed[i+11]=F[j];}
  return {vertices:packed,count:triangles*3,triangles,wallTris,path};
 })();models.set(cacheKey,task);return task;
}

const featureGLSL=`
  layout(location=5) in float aFeature;
  uniform vec4 uMechanisms;
  vec3 animatedPos(vec3 p){
   if(aFeature>.5&&aFeature<1.5){p.z-=.68*uMechanisms.x;}
   if(aFeature>1.5&&aFeature<2.5){
    float t=1.57079632679*uMechanisms.y,c=cos(t),s=sin(t);
    vec2 q=vec2(p.y-.76,p.z-4.78);
    p.y=.76+c*q.x-s*q.y;p.z=4.78+s*q.x+c*q.y;
   }
   if(aFeature>2.5&&aFeature<3.5){p.y=2.14+(p.y-2.14)*max(.0001,uMechanisms.z);}
   if(aFeature>3.5&&aFeature<4.5){p.z+=.46*uMechanisms.w;}
   return p;
  }
  vec3 animatedNormal(vec3 n){
   if(aFeature>1.5&&aFeature<2.5){float t=1.57079632679*uMechanisms.y,c=cos(t),s=sin(t);return vec3(n.x,c*n.y-s*n.z,s*n.y+c*n.z);}
   return n;
  }
 `;
const vertexSrc=`#version 300 es
 precision highp float;
 layout(location=0)in vec3 aPosition;
 layout(location=1)in vec3 aNormal;
 layout(location=2)in vec3 aColor;
 layout(location=3)in float aWall;
 layout(location=4)in float aMat;
 ${featureGLSL}
 uniform mat4 uViewProj; uniform mat4 uLightVP;
 out vec3 vPosition;out vec3 vNormal;out vec3 vColor;out float vWall;out float vMat;out vec4 vShadow;
 void main(){vec3 p=animatedPos(aPosition);vPosition=p;vNormal=animatedNormal(aNormal);vColor=aColor;vWall=aWall;vMat=aMat;vShadow=uLightVP*vec4(p,1.);gl_Position=uViewProj*vec4(p,1.);}`;
const fragmentSrc=`#version 300 es
 precision highp float;
 in vec3 vPosition,vNormal,vColor;in float vWall,vMat;in vec4 vShadow;
 uniform sampler2D uShadow;uniform float uCutHeight,uExposure,uEvening;uniform vec3 uAmbient,uSunColor;
 out vec4 frag;
 float hash31(vec3 p){p=fract(p*.1031);p+=dot(p,p.yzx+33.33);return fract((p.x+p.y)*p.z);}
 float smnoise(vec3 p){vec3 q=floor(p),f=fract(p);f=f*f*(3.-2.*f);
   return mix(mix(mix(hash31(q),hash31(q+vec3(1,0,0)),f.x),mix(hash31(q+vec3(0,1,0)),hash31(q+vec3(1,1,0)),f.x),f.y),
   mix(mix(hash31(q+vec3(0,0,1)),hash31(q+vec3(1,0,1)),f.x),mix(hash31(q+vec3(0,1,1)),hash31(q+vec3(1,1,1)),f.x),f.y),f.z);
 }
 vec3 materialColor(vec3 col,vec3 pos,float id){
  // World-scale micro-patterns are anchored to actual surfaces, never to screen coordinates.
  if(id>0.5&&id<1.5){
   float grain=sin(pos.z*67.0+sin(pos.x*9.0)*2.1+smnoise(pos*3.0)*8.0);
   float knots=smnoise(vec3(pos.x*2.0,pos.y*1.7,pos.z*1.8));
   col*=.92+.095*grain+.065*(knots-.5);
  }else if(id>1.5&&id<2.5){
   float vein=sin(pos.x*18.0+pos.z*15.0+smnoise(pos*5.0)*12.0);
   float stone=smoothstep(.84,.98,abs(vein));col*=1.0-.18*stone;
   col*=.97+.08*smnoise(pos*30.0);
  }else if(id>2.5&&id<3.5){
   float thread=sin(pos.x*180.0)*sin(pos.z*180.0);
   col*=.94+.09*thread+.065*smnoise(pos*43.0);
  }else if(id>6.5&&id<7.5){
   col*=.975+.045*smnoise(pos*38.0);
  }else if(id>7.5&&id<8.5){
   vec2 joint=abs(fract(pos.xz*3.5)-.5);
   float grout=1.-smoothstep(.465,.489,max(joint.x,joint.y));
   col=mix(col*.64,col,grout);col*=.97+.04*smnoise(pos*21.0);
  }else if(id>5.5&&id<6.5){col*=.91+.19*smnoise(pos*16.0);}
  return clamp(col,0.0,1.0);
 }
 void main(){
 if(vWall>.5 && vPosition.y>uCutHeight)discard;
 vec3 n=normalize(vNormal);vec3 sun=normalize(vec3(-.48,.89,.34));float diffuse=max(0.,dot(n,sun));
 vec3 proj=vShadow.xyz/vShadow.w;vec2 uv=proj.xy*.5+.5;float shadow=1.;
 if(uv.x>0.&&uv.x<1.&&uv.y>0.&&uv.y<1.&&proj.z>-1.&&proj.z<1.){
   float projectedDepth=proj.z*.5+.5;float blocked=0.;
   for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++){
     float dep=texture(uShadow,uv+vec2(float(x),float(y))/1536.).r;
     blocked+=projectedDepth-.0018>dep?1.:0.;
   }
   shadow=1.-.68*(blocked/9.);
 }
 vec3 base=pow(materialColor(max(vColor,vec3(0.)),vPosition,vMat),vec3(2.2));
 vec3 lit=uAmbient+uSunColor*diffuse*shadow;
 // Approximate contact darkening near floor intersections and softer gloss on stone/metal.
 float contact=1.0-.115*exp(-max(vPosition.y,0.0)*4.5);
 lit*=contact;
 vec3 halfDir=normalize(vec3(-.48,.89,.34)+vec3(.10,.62,1.0));
 float shine=pow(max(dot(n,halfDir),0.0),vMat>4.5&&vMat<5.5?65.0:28.0);
 float spec=(vMat>4.5&&vMat<5.5)?.25:(vMat>1.5&&vMat<2.5)?.09:.025;
 lit+=vec3(spec*shine*shadow);
 float d1=length(vPosition.xz-vec2(4.03,5.9));float d2=length(vPosition.xz-vec2(4.00,9.4));float d3=length(vPosition.xz-vec2(5.96,2.15));
 vec3 warm=vec3(1.0,.61,.28)*uEvening*(.35*exp(-d1*d1*.37)+.32*exp(-d2*d2*.36)+.28*exp(-d3*d3*.43));
 vec3 c=base*(lit+warm)*uExposure;
 c=(c*(2.51*c+.03))/(c*(2.43*c+.59)+.14);c=pow(clamp(c,0.,1.),vec3(1./2.2));
 frag=vec4(c,1.);
}`;
const depthVertex=`#version 300 es
 precision highp float;
 layout(location=0)in vec3 aPosition;layout(location=3)in float aWall;
 ${featureGLSL}
 uniform mat4 uLightVP;out float vHeight,vWall;
 void main(){vec3 p=animatedPos(aPosition);vHeight=p.y;vWall=aWall;gl_Position=uLightVP*vec4(p,1.);}`;
const depthFragment=`#version 300 es
 precision highp float;
 in float vHeight,vWall;uniform float uCutHeight;
 void main(){if(vWall>.5 && vHeight>uCutHeight)discard;}`;
class Viewer{
 constructor(canvas,context){this.canvas=canvas;this.gl=context;if(!this.gl)throw Error('Ваш браузер или устройство не поддерживает WebGL 2.');
  const gl=this.gl;this.program=this.makeProgram(vertexSrc,fragmentSrc);this.depthProgram=this.makeProgram(depthVertex,depthFragment);
  this.mainU={};for(const key of ['uViewProj','uLightVP','uCutHeight','uExposure','uEvening','uAmbient','uSunColor','uShadow','uMechanisms'])this.mainU[key]=gl.getUniformLocation(this.program,key);
  this.depthU={};for(const key of ['uLightVP','uCutHeight','uMechanisms'])this.depthU[key]=gl.getUniformLocation(this.depthProgram,key);
  this.buf=gl.createBuffer();this.vao=gl.createVertexArray();gl.bindVertexArray(this.vao);gl.bindBuffer(gl.ARRAY_BUFFER,this.buf);for(const [idx,size,offset] of [[0,3,0],[1,3,12],[2,3,24],[3,1,36],[4,1,40],[5,1,44]]){gl.enableVertexAttribArray(idx);gl.vertexAttribPointer(idx,size,gl.FLOAT,false,48,offset);}gl.bindVertexArray(null);
  this.depthTex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.depthTex);gl.texImage2D(gl.TEXTURE_2D,0,gl.DEPTH_COMPONENT24,1536,1536,0,gl.DEPTH_COMPONENT,gl.UNSIGNED_INT,null);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  this.fbo=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,this.fbo);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,this.depthTex,0);gl.drawBuffers([gl.NONE]);gl.readBuffer(gl.NONE);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Ошибка буфера теней');gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);this.model=null;this.id='';this.width=0;this.height=0;this.count=0;this.cameraActive=false;
 }
 makeProgram(v,f){const gl=this.gl;const load=(type,source)=>{const sh=gl.createShader(type);gl.shaderSource(sh,source);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(sh));return sh;};const p=gl.createProgram();gl.attachShader(p,load(gl.VERTEX_SHADER,v));gl.attachShader(p,load(gl.FRAGMENT_SHADER,f));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p;}
 async setModel(name){const model=await loadModel(name);const gl=this.gl;gl.bindBuffer(gl.ARRAY_BUFFER,this.buf);gl.bufferData(gl.ARRAY_BUFFER,model.vertices,gl.STATIC_DRAW);this.model=model;this.id=name;this.count=model.count;this.draw();}
 resize(){const rect=this.canvas.getBoundingClientRect();const dpr=Math.min(window.devicePixelRatio||1,1.7);const w=Math.max(1,Math.round(rect.width*dpr)),h=Math.max(1,Math.round(rect.height*dpr));if(this.width!==w||this.height!==h){this.canvas.width=w;this.canvas.height=h;this.width=w;this.height=h;}return [w,h];}
 draw(){if(!this.model)return;const gl=this.gl,[w,h]=this.resize();const light=lightVP(),cut=ui.cut?1.12:100;gl.bindVertexArray(this.vao);
  // Shadow pass reuses the same vertex buffer and honors the wall cross-section.
  gl.bindFramebuffer(gl.FRAMEBUFFER,this.fbo);gl.viewport(0,0,1536,1536);gl.colorMask(false,false,false,false);gl.clear(gl.DEPTH_BUFFER_BIT);gl.useProgram(this.depthProgram);gl.uniformMatrix4fv(this.depthU.uLightVP,false,light);gl.uniform1f(this.depthU.uCutHeight,cut);gl.uniform4fv(this.depthU.uMechanisms,mechanismVector());gl.drawArrays(gl.TRIANGLES,0,this.count);
  gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.colorMask(true,true,true,true);gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  gl.useProgram(this.program);gl.uniformMatrix4fv(this.mainU.uViewProj,false,cameraVP(w/h));gl.uniformMatrix4fv(this.mainU.uLightVP,false,light);gl.uniform1f(this.mainU.uCutHeight,cut);gl.uniform4fv(this.mainU.uMechanisms,mechanismVector());gl.uniform1f(this.mainU.uExposure,ui.brightness);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.depthTex);gl.uniform1i(this.mainU.uShadow,0);
  const lit={day:{ambient:[.63,.70,.72],sun:[.94,.87,.73],evening:.00},golden:{ambient:[.57,.59,.61],sun:[1.20,.73,.42],evening:.23},evening:{ambient:[.25,.38,.52],sun:[.32,.32,.42],evening:1.0}}[ui.light];
  gl.uniform3fv(this.mainU.uAmbient,lit.ambient);gl.uniform3fv(this.mainU.uSunColor,lit.sun);gl.uniform1f(this.mainU.uEvening,lit.evening);gl.drawArrays(gl.TRIANGLES,0,this.count);gl.bindVertexArray(null);
 }
}


const mechanismVector=()=>new Float32Array([ui.mechanisms.peninsula,ui.mechanisms.laptop,ui.mechanisms.screen,ui.mechanisms.wardrobe]);
function animatedPoint(v,f){if(!f)return v;
 const p=[...v];if(f===1)p[2]-=.68*ui.mechanisms.peninsula;
 else if(f===2){const t=Math.PI/2*ui.mechanisms.laptop,c=Math.cos(t),s=Math.sin(t),y=p[1]-.76,z=p[2]-4.78;p[1]=.76+c*y-s*z;p[2]=4.78+s*y+c*z;}
 else if(f===3)p[1]=2.14+(p[1]-2.14)*Math.max(.0001,ui.mechanisms.screen);
 else if(f===4)p[2]+=.46*ui.mechanisms.wardrobe;
 return p;}
function animatedDirection(v,f){if(f!==2)return v;const t=Math.PI/2*ui.mechanisms.laptop,c=Math.cos(t),s=Math.sin(t);return[v[0],c*v[1]-s*v[2],s*v[1]+c*v[2]];}

// Compatible 2D canvas projection for browsers where WebGL is disabled by GPU policy.
// Projects the actual triangles of our GLB rather than displaying a fake 3D illustration.
class CanvasViewer{
 constructor(canvas){this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:true});if(!this.ctx)throw Error('Устройство не поддерживает рисование Canvas.');this.id='';this.model=null;this.width=0;this.height=0;this.count=0;this.software=true;}
 async setModel(name){const m=await loadModel(name);this.model=m;this.id=name;this.count=m.count;this.draw();}
 resize(){const r=this.canvas.getBoundingClientRect();const dpr=Math.min(window.devicePixelRatio||1,1.4);const w=Math.max(1,Math.floor(r.width*dpr)),h=Math.max(1,Math.floor(r.height*dpr));if(w!==this.width||h!==this.height){this.canvas.width=w;this.canvas.height=h;this.width=w;this.height=h;}return[w,h];}
 draw(){if(!this.model)return;const [w,h]=this.resize(),ctx=this.ctx,packed=this.model.vertices;
  const bg=ctx.createRadialGradient(w*.5,h*.33,30,w*.55,h*.4,Math.max(w,h)*.8);
  if(ui.light==='evening'){bg.addColorStop(0,'#85929b');bg.addColorStop(1,'#394a56');}
  else if(ui.light==='golden'){bg.addColorStop(0,'#f5e9d5');bg.addColorStop(1,'#bcb9af');}
  else{bg.addColorStop(0,'#f6f4ec');bg.addColorStop(1,'#cbd5d2');}
  ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  const proj=cameraVP(w/h),{az,el,dist,target}=camera;
  const eye=[target[0]+dist*Math.cos(el)*Math.sin(az),target[1]+dist*Math.sin(el),target[2]+dist*Math.cos(el)*Math.cos(az)];
  const forward=norm(sub(target,eye));const faces=[];const plane=ui.cut?1.12:100;
  function clipWall(poly){const out=[];for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length],ina=a[1]<=plane,inb=b[1]<=plane;
    if(ina)out.push(a);if(ina!==inb){const t=(plane-a[1])/(b[1]-a[1]);out.push([a[0]+t*(b[0]-a[0]),plane,a[2]+t*(b[2]-a[2])]);}
   }return out;}
  // Clip triangles before perspective projection, otherwise eye-level cameras
  // can produce gigantic polygons when a triangle straddles the near plane.
  const clipNear=(poly,near=.19)=>{
    const out=[];for(let i=0;i<poly.length;i++){
      const a=poly[i],b=poly[(i+1)%poly.length],da=dot(sub(a,eye),forward),db=dot(sub(b,eye),forward);
      const ina=da>=near,inb=db>=near;
      if(ina)out.push(a);
      if(ina!==inb){const t=(near-da)/(db-da);out.push(a.map((v,k)=>v+(b[k]-v)*t));}
    }return out;
  };
  const transform=(p)=>{const x=p[0],y=p[1],z=p[2],xp=proj[0]*x+proj[4]*y+proj[8]*z+proj[12],yp=proj[1]*x+proj[5]*y+proj[9]*z+proj[13],wp=proj[3]*x+proj[7]*y+proj[11]*z+proj[15];
    if(wp<=.02)return null;return[(xp/wp*.5+.5)*w,(-yp/wp*.5+.5)*h];};
  for(let i=0;i<packed.length;i+=36){
    const isWall=packed[i+9]>.5,feature=packed[i+11];
    const a=animatedPoint([packed[i],packed[i+1],packed[i+2]],feature),b=animatedPoint([packed[i+12],packed[i+13],packed[i+14]],feature),c=animatedPoint([packed[i+24],packed[i+25],packed[i+26]],feature);
    const n=animatedDirection([packed[i+3],packed[i+4],packed[i+5]],feature),col=[packed[i+6],packed[i+7],packed[i+8]];
    let poly=isWall&&ui.cut?clipWall([a,b,c]):[a,b,c];poly=clipNear(poly);if(poly.length<3)continue;
    const projected=poly.map(transform);if(projected.some(v=>!v))continue;
    const out=projected.flat();const bounds=[Math.min(...projected.map(v=>v[0])),Math.min(...projected.map(v=>v[1])),Math.max(...projected.map(v=>v[0])),Math.max(...projected.map(v=>v[1]))];
    if(bounds[2]<0||bounds[0]>w||bounds[3]<0||bounds[1]>h)continue;
    const depth=poly.reduce((t,p)=>t+dot(sub(p,eye),forward),0)/poly.length;
    const direct=Math.max(0,dot(n,[-.42,.85,.32]));const lit=ui.light==='day'?.73+.40*direct:ui.light==='golden'?.65+.46*direct:.42+.22*direct;
    let rgb=col.map((v,k)=>Math.round(255*Math.pow(clamp(v*lit*ui.brightness*(ui.light==='evening'&&k===0?1.20:1),0,1),.87)));
    if(ui.light==='evening')rgb=[Math.round(rgb[0]*.90),Math.round(rgb[1]*.95),Math.min(255,Math.round(rgb[2]*1.20))];
    faces.push([depth,projected,'rgb('+rgb.join(',')+')']);
  }
  faces.sort((a,b)=>b[0]-a[0]);ctx.lineWidth=.35;
  for(const [,pts,color] of faces){ctx.beginPath();ctx.moveTo(pts[0][0],pts[0][1]);for(let j=1;j<pts.length;j++)ctx.lineTo(pts[j][0],pts[j][1]);ctx.closePath();ctx.fillStyle=color;ctx.fill();ctx.strokeStyle=color;ctx.stroke();}
 }
}
function makeViewer(canvas){
  const context=canvas.getContext('webgl2',{antialias:true,alpha:true,preserveDrawingBuffer:true});
  if(!context)return new CanvasViewer(canvas);
  try{return new Viewer(canvas,context);}catch(e){
    console.warn('WebGL renderer unavailable; using Canvas fallback:',e);
    // A canvas that has obtained WebGL cannot subsequently obtain a 2D context.
    const replacement=canvas.cloneNode(false);canvas.replaceWith(replacement);
    return new CanvasViewer(replacement);
  }
}

let left=null,right=null,isDragging=false,gestureStart=null,lastPosition=null,activePointers=new Map();
const reDraw=()=>{left?.draw();if(ui.compare)right?.draw();};
const lastError=e=>{console.error(e);$('#loading').hidden=true;$('#modelError').hidden=false;$('#errorText').textContent=e.message||String(e);};

const MECH_LABELS={peninsula:['Выдвинуть поверхность','Убрать поверхность'],laptop:['Открыть зону ноутбука','Закрыть зону ноутбука'],screen:['Опустить экран проектора','Убрать экран проектора'],wardrobe:['Открыть секцию гардеробной','Закрыть секцию гардеробной']};
const MECH_STATUS={peninsula:['Столешница находится под кухонным фронтом','Выдвинутая рабочая поверхность — эскиз'],laptop:['Рабочая консоль закрыта','Откидная консоль раскрыта'],screen:['Проекторный экран свернут','Проекторный экран опущен поверх ТВ'],wardrobe:['Фасад гардеробной закрыт','Фасад шкафа сдвинут; оба дверных проёма свободны']};
function syncMechanismUI(){
 $$('[data-mechanism]').forEach(b=>{const key=b.dataset.mechanism,on=ui.mechanisms[key]>.5;b.textContent=(on?'✓  ':'↗  ')+MECH_LABELS[key][on?1:0];b.setAttribute('aria-pressed',String(on));b.classList.toggle('active',on);b.disabled=ui.mode==='shell';});
 const status=$('#mechanismStatus');if(status)status.textContent=ui.mode==='shell'?'В режиме планировки трансформации скрыты':ui.scenario==='guest'?'Диван разложен: гостевая зона занята':ui.scenario==='dinner'?'Стол накрыт на шесть человек':'Выберите действие, чтобы изменить реальную 3D-геометрию';
 $('#sofaAction').textContent=ui.scenario==='guest'?'Сложить гостевой диван':'Разложить гостевой диван';$('#sofaAction').disabled=ui.mode==='shell';$('#sofaAction').setAttribute('aria-pressed',String(ui.scenario==='guest'));$('#cinemaScene').disabled=ui.mode==='shell';$('#cinemaScene').setAttribute('aria-pressed',String(ui.cinema));$('#cinemaScene').textContent=ui.cinema?'◼ Выключить кинотеатр':'▶ Режим кинотеатра';
}
const activeAnimations=new Map();
function animateMechanism(key,target){const start=ui.mechanisms[key],t0=performance.now(),duration=550,runId=Symbol(key);activeAnimations.set(key,runId);
 const tick=t=>{if(activeAnimations.get(key)!==runId)return;const p=Math.min(1,(t-t0)/duration),ease=p*p*(3-2*p);ui.mechanisms[key]=start+(target-start)*ease;reDraw();if(p<1)requestAnimationFrame(tick);else{ui.mechanisms[key]=target;activeAnimations.delete(key);syncMechanismUI();reDraw();}};
 requestAnimationFrame(tick);
}
function announce(message){const box=$('#sceneNotice');if(!box)return;box.textContent=message;box.hidden=false;clearTimeout(announce.timer);announce.timer=setTimeout(()=>box.hidden=true,4800);}
async function setSofaState(open){if(open){ui.scenario='guest';if(ui.mechanisms.peninsula>.5){ui.mechanisms.peninsula=0;announce('Для гостевого спального места выдвижная поверхность убрана.');}}else ui.scenario='daily';updateStyleUI();syncMechanismUI();await reloadModels();setView('kitchen');}

function updateRoomCard(){const d=ROOM_INFO[ui.view]||ROOM_INFO.whole;$('#selectedRoomCard').innerHTML=`<strong>${d[0]}</strong><span>${d[1]}</span><p>${d[2]}</p>`;}
function updateStyleUI(){
 $$('#styles [data-style]').forEach(b=>{let active=b.dataset.style===ui.style;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
 $('#stageStyleTitle').textContent=STYLE_NAMES[ui.style];const spec=DESIGN_SPEC[ui.style];$('#designSpec').innerHTML=`<b>${spec[0]}</b><span>${spec[1]}</span><p>${spec[2]}</p>`;updateRoomCard();$('#leftModelTag').textContent=STYLE_NAMES[ui.style]+' · '+({now:'детская сейчас',two:'двое малышей',school:'школьный возраст'}[ui.stage]);
 $('#rightModelTag').textContent=STYLE_NAMES[ui.secondStyle];
 $('#stageModeTitle').textContent=ui.mode==='shell'?'ПЛАНИРОВКА':({now:'СЕЙЧАС',two:'ДВОЕ МАЛЫШЕЙ',school:'ШКОЛЬНЫЙ ВОЗРАСТ'}[ui.stage]);
 $('#downloadGLB').href='./models/'+(ui.mode==='shell'?'kvartira-planirovka.glb':`kvartira-${ui.style}-${ui.stage}-${ui.scenario}.glb`);
 $('#downloadGLB').download=ui.mode==='shell'?'kvartira-planirovka.glb':`kvartira-${ui.style}-${ui.stage}-${ui.scenario}.glb`;
 $('#modeInterior').classList.toggle('active',ui.mode!=='shell');$('#modeShell').classList.toggle('active',ui.mode==='shell');
 $('#modeInterior').setAttribute('aria-pressed',String(ui.mode!=='shell'));$('#modeShell').setAttribute('aria-pressed',String(ui.mode==='shell'));
 $$('[data-stage]').forEach(b=>{const a=b.dataset.stage===ui.stage;b.classList.toggle('active',a);b.setAttribute('aria-pressed',String(a));});
 $$('[data-scenario]').forEach(b=>{const a=b.dataset.scenario===ui.scenario;b.classList.toggle('active',a);b.setAttribute('aria-pressed',String(a));});
 syncMechanismUI();$('#modelWrap').classList.toggle('comparing',ui.compare);$('#compareWrap').hidden=!ui.compare;$('#rightModelTag').hidden=!ui.compare;$('#compareSelect').hidden=!ui.compare;
}
let sequence=0;
async function reloadModels(){const seq=++sequence;$('#loading').hidden=false;try{
 const wanted=ui.mode==='shell'?'shell':ui.style;
 const modelA=await loadModel(wanted);if(seq!==sequence)return;await left.setModel(wanted);
 if(ui.compare){const b=ui.mode==='shell'?'shell':ui.secondStyle;await loadModel(b);if(seq!==sequence)return;await right.setModel(b);}
 if(seq===sequence){$('#loading').hidden=true;reDraw();}
 }catch(e){if(seq===sequence)lastError(e);}}
function setView(v){ui.view=v;const d=viewPresets[v]||viewPresets.whole;Object.assign(camera,{...d,target:[...d.target]});$$('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===v));updateRoomCard();reDraw();}
let tourInterval=null,tourPosition=0;
const stops=['whole','kitchen','living','closet','bedroom','bath','balcony'];
function stopTour(){if(tourInterval!==null){clearInterval(tourInterval);tourInterval=null;}$('#guidedTour').textContent='▶ ОБХОД';$('#guidedTour').setAttribute('aria-pressed','false');}
function toggleTour(){if(tourInterval!==null){stopTour();return;}tourPosition=0;setView(stops[tourPosition]);$('#guidedTour').textContent='■ СТОП';$('#guidedTour').setAttribute('aria-pressed','true');tourInterval=setInterval(()=>{tourPosition++;if(tourPosition>=stops.length){stopTour();setView('whole');return;}setView(stops[tourPosition]);},2800);}
function setLightScene(light){ui.light=light;$$('[data-light]').forEach(b=>{const active=b.dataset.light===ui.light;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});$('#modelWrap').style.background=ui.light==='evening'?'radial-gradient(ellipse at 50% 40%,#74828e,#26323a 95%)':ui.light==='golden'?'radial-gradient(ellipse at 50% 40%,#f0ddc5,#c5bdaf 95%)':'';reDraw();}

function zoom(mult){camera.dist=clamp(camera.dist*mult,2.3,42);reDraw();}
function bindPointer(canvas){
 canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);activePointers.set(e.pointerId,[e.clientX,e.clientY]);isDragging=true;});
 canvas.addEventListener('pointermove',e=>{if(!activePointers.has(e.pointerId))return;const old=activePointers.get(e.pointerId);activePointers.set(e.pointerId,[e.clientX,e.clientY]);if(activePointers.size>=2){const vals=[...activePointers.values()];const d=Math.hypot(vals[0][0]-vals[1][0],vals[0][1]-vals[1][1]);if(gestureStart!==null&&gestureStart>0)zoom(clamp(gestureStart/d,.80,1.25));gestureStart=d;return;}
 const dx=e.clientX-old[0],dy=e.clientY-old[1];camera.az-=dx*.006;camera.el=clamp(camera.el+dy*.005,.12,1.565);reDraw();});
 function done(e){activePointers.delete(e.pointerId);if(activePointers.size<2)gestureStart=null;if(activePointers.size===0)isDragging=false;}
 canvas.addEventListener('pointerup',done);canvas.addEventListener('pointercancel',done);
 canvas.addEventListener('wheel',e=>{e.preventDefault();zoom(Math.exp(e.deltaY*.001));},{passive:false});
}
const QUICK_SCENES={family:{scenario:'daily',stage:'now',light:'golden',view:'kitchen',features:[]},guest:{scenario:'guest',stage:'now',light:'evening',view:'kitchen',features:[]},cooking:{scenario:'daily',stage:'now',light:'golden',view:'kitchen',features:['peninsula']},work:{scenario:'daily',stage:'now',light:'day',view:'kitchen',features:['laptop']},movie:{scenario:'daily',stage:'now',light:'evening',view:'kitchen',features:['screen'],cinema:true},school:{scenario:'daily',stage:'school',light:'day',view:'bedroom',features:[]}};
async function applyQuickScene(id){
 const s=QUICK_SCENES[id];if(!s)return;
 ui.mode='interior';ui.compare=false;$('#compareToggle').checked=false;
 ui.scenario=s.scenario;ui.stage=s.stage;ui.cinema=!!s.cinema;
 for(const key of Object.keys(ui.mechanisms)){activeAnimations.delete(key);ui.mechanisms[key]=s.features.includes(key)?1:0;}
 updateStyleUI();setLightScene(s.light);await reloadModels();setView(s.view);
 $$('[data-quick]').forEach(b=>{const active=b.dataset.quick===id;b.setAttribute('aria-pressed',String(active));});
 announce(({family:'Семейный вечер: диван сложен, мягкий свет.',guest:'Гостевое спальное место разложено. Столешница убрана.',cooking:'Выдвинута дополнительная рабочая поверхность.',work:'Открыта консоль ноутбука.',movie:'Проектор опущен. Для затемнения нужны шторы.',school:'Показана детская для школьного возраста.'})[id]);
}
function bindUi(){
 $$('#styles [data-style]').forEach(b=>b.addEventListener('click',async()=>{ui.style=b.dataset.style;updateStyleUI();await reloadModels();}));
 $$('[data-quick]').forEach(b=>b.addEventListener('click',()=>applyQuickScene(b.dataset.quick)));
 $('#guidedTour').onclick=toggleTour;
 $('#modeShell').onclick=async()=>{ui.mode='shell';updateStyleUI();await reloadModels();};$('#modeInterior').onclick=async()=>{ui.mode='interior';updateStyleUI();await reloadModels();};
 $$('[data-stage]').forEach(b=>b.onclick=async()=>{ui.stage=b.dataset.stage;updateStyleUI();await reloadModels();});
 $$('[data-scenario]').forEach(b=>b.onclick=async()=>{ui.scenario=b.dataset.scenario;if(ui.scenario!=='daily'&&ui.mechanisms.peninsula>.5){ui.mechanisms.peninsula=0;announce('Для свободного прохода дополнительная столешница убрана.');}updateStyleUI();await reloadModels();});
 $('#sofaAction').onclick=()=>setSofaState(ui.scenario!=='guest');
 $('#cinemaScene').onclick=()=>{ui.cinema=!ui.cinema;animateMechanism('screen',ui.cinema?1:0);setLightScene(ui.cinema?'evening':'day');syncMechanismUI();setView('kitchen');announce(ui.cinema?'Кинотеатр: вечерний свет и экран. Физическое затемнение окон потребует штор.':'Кинотеатр выключен.');};
 $$('[data-mechanism]').forEach(b=>b.onclick=()=>{const key=b.dataset.mechanism,to=ui.mechanisms[key]>.5?0:1;if(to&&key==='peninsula'&&ui.scenario!=='daily'){announce('Дополнительная поверхность доступна только в повседневном режиме. Сложите диван или обеденный стол.');return;}if(to&&key==='laptop'&&ui.scenario==='dinner'){announce('Для открывания рабочего места сначала сложите шестиместный стол.');return;}animateMechanism(key,to);setView(key==='peninsula'||key==='laptop'||key==='screen'?'kitchen':'closet');});
 $('#compareToggle').onchange=async e=>{ui.compare=e.target.checked;updateStyleUI();await reloadModels();};
 $('#secondStyle').onchange=async e=>{ui.secondStyle=e.target.value;updateStyleUI();await reloadModels();};
 $('#cutToggle').onchange=e=>{ui.cut=e.target.checked;reDraw();};
 $$('[data-light]').forEach(b=>b.onclick=()=>{ui.cinema=false;setLightScene(b.dataset.light);syncMechanismUI();});
 $('#fullscreenBtn').onclick=()=>{const box=$('#modelWrap');if(document.fullscreenElement){document.exitFullscreen?.();}else{box.requestFullscreen?.().catch(()=>{});}};
 document.addEventListener('fullscreenchange',()=>{setTimeout(reDraw,60);});
 $('#exposure').oninput=e=>{ui.brightness=Number(e.target.value)/100;$('#exposureValue').textContent=e.target.value+'%';reDraw();};
 $$('[data-view]').forEach(b=>b.onclick=()=>{stopTour();setView(b.dataset.view);});$('#resetView').onclick=()=>setView('whole');$('#zoomIn').onclick=()=>zoom(.8);$('#zoomOut').onclick=()=>zoom(1.25);
 $('#savePng').onclick=()=>{reDraw();const source=left.canvas;const out=document.createElement('canvas');const ratio=ui.compare?2:1;out.width=source.width*ratio;out.height=source.height;const ctx=out.getContext('2d');ctx.fillStyle=ui.light==='evening'?'#516273':ui.light==='golden'?'#e4d6c6':'#e7e7e1';ctx.fillRect(0,0,out.width,out.height);ctx.drawImage(source,0,0);if(ui.compare)ctx.drawImage(right.canvas,source.width,0,source.width,source.height);const a=document.createElement('a');a.download=`apartments-${ui.style}${ui.compare?'-vs-'+ui.secondStyle:''}-${ui.view}-${ui.light}.png`;a.href=out.toDataURL('image/png');a.click();};
 const ds=[['openSource','sourceDialog'],['openMetrics','metricsDialog'],['openNotes','notesDialog'],['openGallery','galleryDialog']];for(const [button,dialog]of ds)$('#'+button).onclick=()=>$('#'+dialog).showModal();
 $$('[data-close]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.close).close());
 const gallery=()=>{let current='warm',filter='all';const populate=()=>{
  const general=[{file:'apartment_zoning.png',name:'План с двумя входами',type:'general'},
  {file:'parents_now.png',name:'Спальня и проходная гардеробная',type:'general'}];
  const modelViews=['whole','top','kitchen','living','bedroom','bath','hall','closet','balcony'].map((room)=>({file:`model_views/${current}_${room}.webp`,name:({'whole':'Вся квартира','top':'Вид сверху','kitchen':'Кухня-гостиная','living':'Родительская спальня','bedroom':'Детская','bath':'Санузел','hall':'Коридор','closet':'Гардеробная','balcony':'Лоджия'})[room],type:'inside'}));
  const shots=[...general,...modelViews].filter(x=>filter==='all'||filter===x.type);
  $('#galleryGrid').innerHTML=shots.map(s=>`<figure><a href="./assets/${s.file}" target="_blank"><img loading="lazy" src="./assets/${s.file}" alt="${s.name}"/></a><figcaption>${s.name}</figcaption></figure>`).join('');
  $$('[data-g-style]').forEach(b=>{b.classList.toggle('active',b.dataset.gStyle===current);b.setAttribute('aria-pressed',String(b.dataset.gStyle===current));});
  $$('[data-filter]').forEach(b=>{b.classList.toggle('active',b.dataset.filter===filter);b.setAttribute('aria-pressed',String(b.dataset.filter===filter));});
 };$$('[data-g-style]').forEach(b=>b.onclick=()=>{current=b.dataset.gStyle;populate();});
 $$('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;populate();});populate();};gallery();
 window.addEventListener('resize',reDraw);
}
async function start(){try{left=makeViewer($('#mainCanvas'));right=makeViewer($('#compareCanvas'));bindPointer(left.canvas);bindPointer(right.canvas);bindUi();const url=new URLSearchParams(window.location.search);for(const [key,choices] of [['style',['warm','japandi','graphite']],['stage',['now','two','school']],['scenario',['daily','guest','dinner']]]){const v=url.get(key);if(choices.includes(v))ui[key]=v;}updateStyleUI();await reloadModels();if(QUICK_SCENES[url.get('scene')])await applyQuickScene(url.get('scene'));else{const view=url.get('view');if(view && viewPresets[view])setView(view);} const light=url.get('light');if(['day','golden','evening'].includes(light) && !QUICK_SCENES[url.get('scene')])setLightScene(light);window.__atelier={getState:()=>({...ui,mechanisms:{...ui.mechanisms},software:left.software||false}),setStyle:async(id)=>{ui.style=id;updateStyleUI();await reloadModels();},setView,draw:reDraw,setSofaState,setMechanism:async(key,on)=>{if(!(key in ui.mechanisms))throw Error('Неизвестный механизм');ui.mechanisms[key]=on?1:0;syncMechanismUI();reDraw();},applyQuickScene,meshStats:()=>left.model&&({triangles:left.model.triangles,wallTriangles:left.model.wallTris})};}catch(e){lastError(e);}}
start();
