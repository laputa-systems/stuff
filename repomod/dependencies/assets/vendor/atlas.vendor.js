var AtlasVendor=(()=>{var Ki=Object.create;var Wt=Object.defineProperty;var Zi=Object.getOwnPropertyDescriptor;var Qi=Object.getOwnPropertyNames;var Ji=Object.getPrototypeOf,eo=Object.prototype.hasOwnProperty;var Aa=(a,n)=>()=>(n||a((n={exports:{}}).exports,n),n.exports),to=(a,n)=>{for(var t in n)Wt(a,t,{get:n[t],enumerable:!0})},Da=(a,n,t,e)=>{if(n&&typeof n=="object"||typeof n=="function")for(let r of Qi(n))!eo.call(a,r)&&r!==t&&Wt(a,r,{get:()=>n[r],enumerable:!(e=Zi(n,r))||e.enumerable});return a};var Me=(a,n,t)=>(t=a!=null?Ki(Ji(a)):{},Da(n||!a||!a.__esModule?Wt(t,"default",{value:a,enumerable:!0}):t,a)),no=a=>Da(Wt({},"__esModule",{value:!0}),a);var Ke=Aa((Bd,kn)=>{"use strict";var Ye=typeof Reflect=="object"?Reflect:null,wa=Ye&&typeof Ye.apply=="function"?Ye.apply:function(n,t,e){return Function.prototype.apply.call(n,t,e)},Ot;Ye&&typeof Ye.ownKeys=="function"?Ot=Ye.ownKeys:Object.getOwnPropertySymbols?Ot=function(n){return Object.getOwnPropertyNames(n).concat(Object.getOwnPropertySymbols(n))}:Ot=function(n){return Object.getOwnPropertyNames(n)};function ao(a){console&&console.warn&&console.warn(a)}var Ca=Number.isNaN||function(n){return n!==n};function J(){J.init.call(this)}kn.exports=J;kn.exports.once=so;J.EventEmitter=J;J.prototype._events=void 0;J.prototype._eventsCount=0;J.prototype._maxListeners=void 0;var La=10;function Ut(a){if(typeof a!="function")throw new TypeError('The "listener" argument must be of type Function. Received type '+typeof a)}Object.defineProperty(J,"defaultMaxListeners",{enumerable:!0,get:function(){return La},set:function(a){if(typeof a!="number"||a<0||Ca(a))throw new RangeError('The value of "defaultMaxListeners" is out of range. It must be a non-negative number. Received '+a+".");La=a}});J.init=function(){(this._events===void 0||this._events===Object.getPrototypeOf(this)._events)&&(this._events=Object.create(null),this._eventsCount=0),this._maxListeners=this._maxListeners||void 0};J.prototype.setMaxListeners=function(n){if(typeof n!="number"||n<0||Ca(n))throw new RangeError('The value of "n" is out of range. It must be a non-negative number. Received '+n+".");return this._maxListeners=n,this};function Pa(a){return a._maxListeners===void 0?J.defaultMaxListeners:a._maxListeners}J.prototype.getMaxListeners=function(){return Pa(this)};J.prototype.emit=function(n){for(var t=[],e=1;e<arguments.length;e++)t.push(arguments[e]);var r=n==="error",i=this._events;if(i!==void 0)r=r&&i.error===void 0;else if(!r)return!1;if(r){var o;if(t.length>0&&(o=t[0]),o instanceof Error)throw o;var s=new Error("Unhandled error."+(o?" ("+o.message+")":""));throw s.context=o,s}var l=i[n];if(l===void 0)return!1;if(typeof l=="function")wa(l,this,t);else for(var u=l.length,d=Ga(l,u),e=0;e<u;++e)wa(d[e],this,t);return!0};function ka(a,n,t,e){var r,i,o;if(Ut(t),i=a._events,i===void 0?(i=a._events=Object.create(null),a._eventsCount=0):(i.newListener!==void 0&&(a.emit("newListener",n,t.listener?t.listener:t),i=a._events),o=i[n]),o===void 0)o=i[n]=t,++a._eventsCount;else if(typeof o=="function"?o=i[n]=e?[t,o]:[o,t]:e?o.unshift(t):o.push(t),r=Pa(a),r>0&&o.length>r&&!o.warned){o.warned=!0;var s=new Error("Possible EventEmitter memory leak detected. "+o.length+" "+String(n)+" listeners added. Use emitter.setMaxListeners() to increase limit");s.name="MaxListenersExceededWarning",s.emitter=a,s.type=n,s.count=o.length,ao(s)}return a}J.prototype.addListener=function(n,t){return ka(this,n,t,!1)};J.prototype.on=J.prototype.addListener;J.prototype.prependListener=function(n,t){return ka(this,n,t,!0)};function ro(){if(!this.fired)return this.target.removeListener(this.type,this.wrapFn),this.fired=!0,arguments.length===0?this.listener.call(this.target):this.listener.apply(this.target,arguments)}function Fa(a,n,t){var e={fired:!1,wrapFn:void 0,target:a,type:n,listener:t},r=ro.bind(e);return r.listener=t,e.wrapFn=r,r}J.prototype.once=function(n,t){return Ut(t),this.on(n,Fa(this,n,t)),this};J.prototype.prependOnceListener=function(n,t){return Ut(t),this.prependListener(n,Fa(this,n,t)),this};J.prototype.removeListener=function(n,t){var e,r,i,o,s;if(Ut(t),r=this._events,r===void 0)return this;if(e=r[n],e===void 0)return this;if(e===t||e.listener===t)--this._eventsCount===0?this._events=Object.create(null):(delete r[n],r.removeListener&&this.emit("removeListener",n,e.listener||t));else if(typeof e!="function"){for(i=-1,o=e.length-1;o>=0;o--)if(e[o]===t||e[o].listener===t){s=e[o].listener,i=o;break}if(i<0)return this;i===0?e.shift():io(e,i),e.length===1&&(r[n]=e[0]),r.removeListener!==void 0&&this.emit("removeListener",n,s||t)}return this};J.prototype.off=J.prototype.removeListener;J.prototype.removeAllListeners=function(n){var t,e,r;if(e=this._events,e===void 0)return this;if(e.removeListener===void 0)return arguments.length===0?(this._events=Object.create(null),this._eventsCount=0):e[n]!==void 0&&(--this._eventsCount===0?this._events=Object.create(null):delete e[n]),this;if(arguments.length===0){var i=Object.keys(e),o;for(r=0;r<i.length;++r)o=i[r],o!=="removeListener"&&this.removeAllListeners(o);return this.removeAllListeners("removeListener"),this._events=Object.create(null),this._eventsCount=0,this}if(t=e[n],typeof t=="function")this.removeListener(n,t);else if(t!==void 0)for(r=t.length-1;r>=0;r--)this.removeListener(n,t[r]);return this};function Ia(a,n,t){var e=a._events;if(e===void 0)return[];var r=e[n];return r===void 0?[]:typeof r=="function"?t?[r.listener||r]:[r]:t?oo(r):Ga(r,r.length)}J.prototype.listeners=function(n){return Ia(this,n,!0)};J.prototype.rawListeners=function(n){return Ia(this,n,!1)};J.listenerCount=function(a,n){return typeof a.listenerCount=="function"?a.listenerCount(n):Na.call(a,n)};J.prototype.listenerCount=Na;function Na(a){var n=this._events;if(n!==void 0){var t=n[a];if(typeof t=="function")return 1;if(t!==void 0)return t.length}return 0}J.prototype.eventNames=function(){return this._eventsCount>0?Ot(this._events):[]};function Ga(a,n){for(var t=new Array(n),e=0;e<n;++e)t[e]=a[e];return t}function io(a,n){for(;n+1<a.length;n++)a[n]=a[n+1];a.pop()}function oo(a){for(var n=new Array(a.length),t=0;t<n.length;++t)n[t]=a[t].listener||a[t];return n}function so(a,n){return new Promise(function(t,e){function r(o){a.removeListener(n,i),e(o)}function i(){typeof a.removeListener=="function"&&a.removeListener("error",r),t([].slice.call(arguments))}za(a,n,i,{once:!0}),n!=="error"&&lo(a,r,{once:!0})})}function lo(a,n,t){typeof a.on=="function"&&za(a,"error",n,t)}function za(a,n,t,e){if(typeof a.on=="function")e.once?a.once(n,t):a.on(n,t);else if(typeof a.addEventListener=="function")a.addEventListener(n,function r(i){e.once&&a.removeEventListener(n,r),t(i)});else throw new TypeError('The "emitter" argument must be of type EventEmitter. Received type '+typeof a)}});var na=Aa((Jd,Dr)=>{Dr.exports=function(n){return n!==null&&typeof n=="object"&&typeof n.addUndirectedEdgeWithKey=="function"&&typeof n.dropNode=="function"&&typeof n.multi=="boolean"}});var zd={};to(zd,{Graph:()=>ee,Sigma:()=>Ui,extremityArrow:()=>Hi,layerPlain:()=>Te,pathLine:()=>Rt});var Oa=Me(Ke(),1);function uo(){let a=arguments[0];for(let n=1,t=arguments.length;n<t;n++)if(arguments[n])for(let e in arguments[n])a[e]=arguments[n][e];return a}var re=uo;typeof Object.assign=="function"&&(re=Object.assign);function fe(a,n,t,e){let r=a._nodes.get(n),i=null;return r&&(e==="mixed"?i=r.out&&r.out[t]||r.undirected&&r.undirected[t]:e==="directed"?i=r.out&&r.out[t]:i=r.undirected&&r.undirected[t]),i}function oe(a){return typeof a=="object"&&a!==null}function Ua(a){let n;for(n in a)return!1;return!0}function he(a,n,t){Object.defineProperty(a,n,{enumerable:!1,configurable:!1,writable:!0,value:t})}function ye(a,n,t){let e={enumerable:!0,configurable:!0};typeof t=="function"?e.get=t:(e.value=t,e.writable=!1),Object.defineProperty(a,n,e)}function Ma(a){return!(!oe(a)||a.attributes&&!Array.isArray(a.attributes))}function co(){let a=Math.floor(Math.random()*256)&255;return()=>a++}function Ae(){let a=arguments,n=null,t=-1;return{[Symbol.iterator](){return this},next(){let e=null;do{if(n===null){if(t++,t>=a.length)return{done:!0};n=a[t][Symbol.iterator]()}if(e=n.next(),e.done){n=null;continue}break}while(!0);return e}}}function Qe(){return{[Symbol.iterator](){return this},next(){return{done:!0}}}}var Tt=class extends Error{constructor(n){super(),this.name="GraphError",this.message=n}},O=class a extends Tt{constructor(n){super(n),this.name="InvalidArgumentsGraphError",typeof Error.captureStackTrace=="function"&&Error.captureStackTrace(this,a.prototype.constructor)}},W=class a extends Tt{constructor(n){super(n),this.name="NotFoundGraphError",typeof Error.captureStackTrace=="function"&&Error.captureStackTrace(this,a.prototype.constructor)}},V=class a extends Tt{constructor(n){super(n),this.name="UsageGraphError",typeof Error.captureStackTrace=="function"&&Error.captureStackTrace(this,a.prototype.constructor)}};function Ha(a,n){this.key=a,this.attributes=n,this.clear()}Ha.prototype.clear=function(){this.inDegree=0,this.outDegree=0,this.undirectedDegree=0,this.undirectedLoops=0,this.directedLoops=0,this.in={},this.out={},this.undirected={}};function $a(a,n){this.key=a,this.attributes=n,this.clear()}$a.prototype.clear=function(){this.inDegree=0,this.outDegree=0,this.directedLoops=0,this.in={},this.out={}};function Va(a,n){this.key=a,this.attributes=n,this.clear()}Va.prototype.clear=function(){this.undirectedDegree=0,this.undirectedLoops=0,this.undirected={}};function Je(a,n,t,e,r){this.key=n,this.attributes=r,this.undirected=a,this.source=t,this.target=e}Je.prototype.attach=function(){let a="out",n="in";this.undirected&&(a=n="undirected");let t=this.source.key,e=this.target.key;this.source[a][e]=this,!(this.undirected&&t===e)&&(this.target[n][t]=this)};Je.prototype.attachMulti=function(){let a="out",n="in",t=this.source.key,e=this.target.key;this.undirected&&(a=n="undirected");let r=this.source[a],i=r[e];if(typeof i>"u"){r[e]=this,this.undirected&&t===e||(this.target[n][t]=this);return}i.previous=this,this.next=i,r[e]=this,this.target[n][t]=this};Je.prototype.detach=function(){let a=this.source.key,n=this.target.key,t="out",e="in";this.undirected&&(t=e="undirected"),delete this.source[t][n],delete this.target[e][a]};Je.prototype.detachMulti=function(){let a=this.source.key,n=this.target.key,t="out",e="in";this.undirected&&(t=e="undirected"),this.previous===void 0?this.next===void 0?(delete this.source[t][n],delete this.target[e][a]):(this.next.previous=void 0,this.source[t][n]=this.next,this.target[e][a]=this.next):(this.previous.next=this.next,this.next!==void 0&&(this.next.previous=this.previous))};var Xa=0,ja=1,ho=2,qa=3;function De(a,n,t,e,r,i,o){let s,l,u,d;if(e=""+e,t===Xa){if(s=a._nodes.get(e),!s)throw new W(`Graph.${n}: could not find the "${e}" node in the graph.`);u=r,d=i}else if(t===qa){if(r=""+r,l=a._edges.get(r),!l)throw new W(`Graph.${n}: could not find the "${r}" edge in the graph.`);let c=l.source.key,f=l.target.key;if(e===c)s=l.target;else if(e===f)s=l.source;else throw new W(`Graph.${n}: the "${e}" node is not attached to the "${r}" edge (${c}, ${f}).`);u=i,d=o}else{if(l=a._edges.get(e),!l)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`);t===ja?s=l.source:s=l.target,u=r,d=i}return[s,u,d]}function fo(a,n,t){a.prototype[n]=function(e,r,i){let[o,s]=De(this,n,t,e,r,i);return o.attributes[s]}}function go(a,n,t){a.prototype[n]=function(e,r){let[i]=De(this,n,t,e,r);return i.attributes}}function vo(a,n,t){a.prototype[n]=function(e,r,i){let[o,s]=De(this,n,t,e,r,i);return o.attributes.hasOwnProperty(s)}}function po(a,n,t){a.prototype[n]=function(e,r,i,o){let[s,l,u]=De(this,n,t,e,r,i,o);return s.attributes[l]=u,this.emit("nodeAttributesUpdated",{key:s.key,type:"set",attributes:s.attributes,name:l}),this}}function mo(a,n,t){a.prototype[n]=function(e,r,i,o){let[s,l,u]=De(this,n,t,e,r,i,o);if(typeof u!="function")throw new O(`Graph.${n}: updater should be a function.`);let d=s.attributes,c=u(d[l]);return d[l]=c,this.emit("nodeAttributesUpdated",{key:s.key,type:"set",attributes:s.attributes,name:l}),this}}function bo(a,n,t){a.prototype[n]=function(e,r,i){let[o,s]=De(this,n,t,e,r,i);return delete o.attributes[s],this.emit("nodeAttributesUpdated",{key:o.key,type:"remove",attributes:o.attributes,name:s}),this}}function yo(a,n,t){a.prototype[n]=function(e,r,i){let[o,s]=De(this,n,t,e,r,i);if(!oe(s))throw new O(`Graph.${n}: provided attributes are not a plain object.`);return o.attributes=s,this.emit("nodeAttributesUpdated",{key:o.key,type:"replace",attributes:o.attributes}),this}}function xo(a,n,t){a.prototype[n]=function(e,r,i){let[o,s]=De(this,n,t,e,r,i);if(!oe(s))throw new O(`Graph.${n}: provided attributes are not a plain object.`);return re(o.attributes,s),this.emit("nodeAttributesUpdated",{key:o.key,type:"merge",attributes:o.attributes,data:s}),this}}function _o(a,n,t){a.prototype[n]=function(e,r,i){let[o,s]=De(this,n,t,e,r,i);if(typeof s!="function")throw new O(`Graph.${n}: provided updater is not a function.`);return o.attributes=s(o.attributes),this.emit("nodeAttributesUpdated",{key:o.key,type:"update",attributes:o.attributes}),this}}var To=[{name:a=>`get${a}Attribute`,attacher:fo},{name:a=>`get${a}Attributes`,attacher:go},{name:a=>`has${a}Attribute`,attacher:vo},{name:a=>`set${a}Attribute`,attacher:po},{name:a=>`update${a}Attribute`,attacher:mo},{name:a=>`remove${a}Attribute`,attacher:bo},{name:a=>`replace${a}Attributes`,attacher:yo},{name:a=>`merge${a}Attributes`,attacher:xo},{name:a=>`update${a}Attributes`,attacher:_o}];function So(a){To.forEach(function({name:n,attacher:t}){t(a,n("Node"),Xa),t(a,n("Source"),ja),t(a,n("Target"),ho),t(a,n("Opposite"),qa)})}function Eo(a,n,t){a.prototype[n]=function(e,r){let i;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>2){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let o=""+e,s=""+r;if(r=arguments[2],i=fe(this,o,s,t),!i)throw new W(`Graph.${n}: could not find an edge for the given path ("${o}" - "${s}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,i=this._edges.get(e),!i)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}return i.attributes[r]}}function Ro(a,n,t){a.prototype[n]=function(e){let r;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>1){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let i=""+e,o=""+arguments[1];if(r=fe(this,i,o,t),!r)throw new W(`Graph.${n}: could not find an edge for the given path ("${i}" - "${o}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,r=this._edges.get(e),!r)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}return r.attributes}}function Ao(a,n,t){a.prototype[n]=function(e,r){let i;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>2){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let o=""+e,s=""+r;if(r=arguments[2],i=fe(this,o,s,t),!i)throw new W(`Graph.${n}: could not find an edge for the given path ("${o}" - "${s}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,i=this._edges.get(e),!i)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}return i.attributes.hasOwnProperty(r)}}function Do(a,n,t){a.prototype[n]=function(e,r,i){let o;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>3){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let s=""+e,l=""+r;if(r=arguments[2],i=arguments[3],o=fe(this,s,l,t),!o)throw new W(`Graph.${n}: could not find an edge for the given path ("${s}" - "${l}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,o=this._edges.get(e),!o)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}return o.attributes[r]=i,this.emit("edgeAttributesUpdated",{key:o.key,type:"set",attributes:o.attributes,name:r}),this}}function wo(a,n,t){a.prototype[n]=function(e,r,i){let o;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>3){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let s=""+e,l=""+r;if(r=arguments[2],i=arguments[3],o=fe(this,s,l,t),!o)throw new W(`Graph.${n}: could not find an edge for the given path ("${s}" - "${l}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,o=this._edges.get(e),!o)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}if(typeof i!="function")throw new O(`Graph.${n}: updater should be a function.`);return o.attributes[r]=i(o.attributes[r]),this.emit("edgeAttributesUpdated",{key:o.key,type:"set",attributes:o.attributes,name:r}),this}}function Lo(a,n,t){a.prototype[n]=function(e,r){let i;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>2){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let o=""+e,s=""+r;if(r=arguments[2],i=fe(this,o,s,t),!i)throw new W(`Graph.${n}: could not find an edge for the given path ("${o}" - "${s}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,i=this._edges.get(e),!i)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}return delete i.attributes[r],this.emit("edgeAttributesUpdated",{key:i.key,type:"remove",attributes:i.attributes,name:r}),this}}function Co(a,n,t){a.prototype[n]=function(e,r){let i;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>2){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let o=""+e,s=""+r;if(r=arguments[2],i=fe(this,o,s,t),!i)throw new W(`Graph.${n}: could not find an edge for the given path ("${o}" - "${s}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,i=this._edges.get(e),!i)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}if(!oe(r))throw new O(`Graph.${n}: provided attributes are not a plain object.`);return i.attributes=r,this.emit("edgeAttributesUpdated",{key:i.key,type:"replace",attributes:i.attributes}),this}}function Po(a,n,t){a.prototype[n]=function(e,r){let i;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>2){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let o=""+e,s=""+r;if(r=arguments[2],i=fe(this,o,s,t),!i)throw new W(`Graph.${n}: could not find an edge for the given path ("${o}" - "${s}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,i=this._edges.get(e),!i)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}if(!oe(r))throw new O(`Graph.${n}: provided attributes are not a plain object.`);return re(i.attributes,r),this.emit("edgeAttributesUpdated",{key:i.key,type:"merge",attributes:i.attributes,data:r}),this}}function ko(a,n,t){a.prototype[n]=function(e,r){let i;if(this.type!=="mixed"&&t!=="mixed"&&t!==this.type)throw new V(`Graph.${n}: cannot find this type of edges in your ${this.type} graph.`);if(arguments.length>2){if(this.multi)throw new V(`Graph.${n}: cannot use a {source,target} combo when asking about an edge's attributes in a MultiGraph since we cannot infer the one you want information about.`);let o=""+e,s=""+r;if(r=arguments[2],i=fe(this,o,s,t),!i)throw new W(`Graph.${n}: could not find an edge for the given path ("${o}" - "${s}").`)}else{if(t!=="mixed")throw new V(`Graph.${n}: calling this method with only a key (vs. a source and target) does not make sense since an edge with this key could have the other type.`);if(e=""+e,i=this._edges.get(e),!i)throw new W(`Graph.${n}: could not find the "${e}" edge in the graph.`)}if(typeof r!="function")throw new O(`Graph.${n}: provided updater is not a function.`);return i.attributes=r(i.attributes),this.emit("edgeAttributesUpdated",{key:i.key,type:"update",attributes:i.attributes}),this}}var Fo=[{name:a=>`get${a}Attribute`,attacher:Eo},{name:a=>`get${a}Attributes`,attacher:Ro},{name:a=>`has${a}Attribute`,attacher:Ao},{name:a=>`set${a}Attribute`,attacher:Do},{name:a=>`update${a}Attribute`,attacher:wo},{name:a=>`remove${a}Attribute`,attacher:Lo},{name:a=>`replace${a}Attributes`,attacher:Co},{name:a=>`merge${a}Attributes`,attacher:Po},{name:a=>`update${a}Attributes`,attacher:ko}];function Io(a){Fo.forEach(function({name:n,attacher:t}){t(a,n("Edge"),"mixed"),t(a,n("DirectedEdge"),"directed"),t(a,n("UndirectedEdge"),"undirected")})}var No=[{name:"edges",type:"mixed"},{name:"inEdges",type:"directed",direction:"in"},{name:"outEdges",type:"directed",direction:"out"},{name:"inboundEdges",type:"mixed",direction:"in"},{name:"outboundEdges",type:"mixed",direction:"out"},{name:"directedEdges",type:"directed"},{name:"undirectedEdges",type:"undirected"}];function Go(a,n,t,e){let r=!1;for(let i in n){if(i===e)continue;let o=n[i];if(r=t(o.key,o.attributes,o.source.key,o.target.key,o.source.attributes,o.target.attributes,o.undirected),a&&r)return o.key}}function zo(a,n,t,e){let r,i,o,s=!1;for(let l in n)if(l!==e){r=n[l];do{if(i=r.source,o=r.target,s=t(r.key,r.attributes,i.key,o.key,i.attributes,o.attributes,r.undirected),a&&s)return r.key;r=r.next}while(r!==void 0)}}function Fn(a,n){let t=Object.keys(a),e=t.length,r,i=0;return{[Symbol.iterator](){return this},next(){do if(r)r=r.next;else{if(i>=e)return{done:!0};let o=t[i++];if(o===n){r=void 0;continue}r=a[o]}while(!r);return{done:!1,value:{edge:r.key,attributes:r.attributes,source:r.source.key,target:r.target.key,sourceAttributes:r.source.attributes,targetAttributes:r.target.attributes,undirected:r.undirected}}}}}function Mo(a,n,t,e){let r=n[t];if(!r)return;let i=r.source,o=r.target;if(e(r.key,r.attributes,i.key,o.key,i.attributes,o.attributes,r.undirected)&&a)return r.key}function Bo(a,n,t,e){let r=n[t];if(!r)return;let i=!1;do{if(i=e(r.key,r.attributes,r.source.key,r.target.key,r.source.attributes,r.target.attributes,r.undirected),a&&i)return r.key;r=r.next}while(r!==void 0)}function In(a,n){let t=a[n];if(t.next!==void 0)return{[Symbol.iterator](){return this},next(){if(!t)return{done:!0};let r={edge:t.key,attributes:t.attributes,source:t.source.key,target:t.target.key,sourceAttributes:t.source.attributes,targetAttributes:t.target.attributes,undirected:t.undirected};return t=t.next,{done:!1,value:r}}};let e=!1;return{[Symbol.iterator](){return this},next(){return e===!0?{done:!0}:(e=!0,{done:!1,value:{edge:t.key,attributes:t.attributes,source:t.source.key,target:t.target.key,sourceAttributes:t.source.attributes,targetAttributes:t.target.attributes,undirected:t.undirected}})}}}function Wo(a,n){if(a.size===0)return[];if(n==="mixed"||n===a.type)return Array.from(a._edges.keys());let t=n==="undirected"?a.undirectedSize:a.directedSize,e=new Array(t),r=n==="undirected",i=a._edges.values(),o=0,s,l;for(;s=i.next(),s.done!==!0;)l=s.value,l.undirected===r&&(e[o++]=l.key);return e}function Ya(a,n,t,e){if(n.size===0)return;let r=t!=="mixed"&&t!==n.type,i=t==="undirected",o,s,l=!1,u=n._edges.values();for(;o=u.next(),o.done!==!0;){if(s=o.value,r&&s.undirected!==i)continue;let{key:d,attributes:c,source:f,target:h}=s;if(l=e(d,c,f.key,h.key,f.attributes,h.attributes,s.undirected),a&&l)return d}}function Oo(a,n){if(a.size===0)return Qe();let t=n!=="mixed"&&n!==a.type,e=n==="undirected",r=a._edges.values();return{[Symbol.iterator](){return this},next(){let i,o;for(;;){if(i=r.next(),i.done)return i;if(o=i.value,!(t&&o.undirected!==e))break}return{value:{edge:o.key,attributes:o.attributes,source:o.source.key,target:o.target.key,sourceAttributes:o.source.attributes,targetAttributes:o.target.attributes,undirected:o.undirected},done:!1}}}}function Nn(a,n,t,e,r,i){let o=n?zo:Go,s;if(t!=="undirected"&&(e!=="out"&&(s=o(a,r.in,i),a&&s)||e!=="in"&&(s=o(a,r.out,i,e?void 0:r.key),a&&s))||t!=="directed"&&(s=o(a,r.undirected,i),a&&s))return s}function Uo(a,n,t,e){let r=[];return Nn(!1,a,n,t,e,function(i){r.push(i)}),r}function Ho(a,n,t){let e=Qe();return a!=="undirected"&&(n!=="out"&&typeof t.in<"u"&&(e=Ae(e,Fn(t.in))),n!=="in"&&typeof t.out<"u"&&(e=Ae(e,Fn(t.out,n?void 0:t.key)))),a!=="directed"&&typeof t.undirected<"u"&&(e=Ae(e,Fn(t.undirected))),e}function Gn(a,n,t,e,r,i,o){let s=t?Bo:Mo,l;if(n!=="undirected"&&(typeof r.in<"u"&&e!=="out"&&(l=s(a,r.in,i,o),a&&l)||typeof r.out<"u"&&e!=="in"&&(e||r.key!==i)&&(l=s(a,r.out,i,o),a&&l))||n!=="directed"&&typeof r.undirected<"u"&&(l=s(a,r.undirected,i,o),a&&l))return l}function $o(a,n,t,e,r){let i=[];return Gn(!1,a,n,t,e,r,function(o){i.push(o)}),i}function Vo(a,n,t,e){let r=Qe();return a!=="undirected"&&(typeof t.in<"u"&&n!=="out"&&e in t.in&&(r=Ae(r,In(t.in,e))),typeof t.out<"u"&&n!=="in"&&e in t.out&&(n||t.key!==e)&&(r=Ae(r,In(t.out,e)))),a!=="directed"&&typeof t.undirected<"u"&&e in t.undirected&&(r=Ae(r,In(t.undirected,e))),r}function Xo(a,n){let{name:t,type:e,direction:r}=n;a.prototype[t]=function(i,o){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return[];if(!arguments.length)return Wo(this,e);if(arguments.length===1){i=""+i;let s=this._nodes.get(i);if(typeof s>"u")throw new W(`Graph.${t}: could not find the "${i}" node in the graph.`);return Uo(this.multi,e==="mixed"?this.type:e,r,s)}if(arguments.length===2){i=""+i,o=""+o;let s=this._nodes.get(i);if(!s)throw new W(`Graph.${t}:  could not find the "${i}" source node in the graph.`);if(!this._nodes.has(o))throw new W(`Graph.${t}:  could not find the "${o}" target node in the graph.`);return $o(e,this.multi,r,s,o)}throw new O(`Graph.${t}: too many arguments (expecting 0, 1 or 2 and got ${arguments.length}).`)}}function jo(a,n){let{name:t,type:e,direction:r}=n,i="forEach"+t[0].toUpperCase()+t.slice(1,-1);a.prototype[i]=function(u,d,c){if(!(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)){if(arguments.length===1)return c=u,Ya(!1,this,e,c);if(arguments.length===2){u=""+u,c=d;let f=this._nodes.get(u);if(typeof f>"u")throw new W(`Graph.${i}: could not find the "${u}" node in the graph.`);return Nn(!1,this.multi,e==="mixed"?this.type:e,r,f,c)}if(arguments.length===3){u=""+u,d=""+d;let f=this._nodes.get(u);if(!f)throw new W(`Graph.${i}:  could not find the "${u}" source node in the graph.`);if(!this._nodes.has(d))throw new W(`Graph.${i}:  could not find the "${d}" target node in the graph.`);return Gn(!1,e,this.multi,r,f,d,c)}throw new O(`Graph.${i}: too many arguments (expecting 1, 2 or 3 and got ${arguments.length}).`)}};let o="map"+t[0].toUpperCase()+t.slice(1);a.prototype[o]=function(){let u=Array.prototype.slice.call(arguments),d=u.pop(),c;if(u.length===0){let f=0;e!=="directed"&&(f+=this.undirectedSize),e!=="undirected"&&(f+=this.directedSize),c=new Array(f);let h=0;u.push((g,m,p,v,b,y,T)=>{c[h++]=d(g,m,p,v,b,y,T)})}else c=[],u.push((f,h,g,m,p,v,b)=>{c.push(d(f,h,g,m,p,v,b))});return this[i].apply(this,u),c};let s="filter"+t[0].toUpperCase()+t.slice(1);a.prototype[s]=function(){let u=Array.prototype.slice.call(arguments),d=u.pop(),c=[];return u.push((f,h,g,m,p,v,b)=>{d(f,h,g,m,p,v,b)&&c.push(f)}),this[i].apply(this,u),c};let l="reduce"+t[0].toUpperCase()+t.slice(1);a.prototype[l]=function(){let u=Array.prototype.slice.call(arguments);if(u.length<2||u.length>4)throw new O(`Graph.${l}: invalid number of arguments (expecting 2, 3 or 4 and got ${u.length}).`);if(typeof u[u.length-1]=="function"&&typeof u[u.length-2]!="function")throw new O(`Graph.${l}: missing initial value. You must provide it because the callback takes more than one argument and we cannot infer the initial value from the first iteration, as you could with a simple array.`);let d,c;u.length===2?(d=u[0],c=u[1],u=[]):u.length===3?(d=u[1],c=u[2],u=[u[0]]):u.length===4&&(d=u[2],c=u[3],u=[u[0],u[1]]);let f=c;return u.push((h,g,m,p,v,b,y)=>{f=d(f,h,g,m,p,v,b,y)}),this[i].apply(this,u),f}}function qo(a,n){let{name:t,type:e,direction:r}=n,i="find"+t[0].toUpperCase()+t.slice(1,-1);a.prototype[i]=function(l,u,d){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return!1;if(arguments.length===1)return d=l,Ya(!0,this,e,d);if(arguments.length===2){l=""+l,d=u;let c=this._nodes.get(l);if(typeof c>"u")throw new W(`Graph.${i}: could not find the "${l}" node in the graph.`);return Nn(!0,this.multi,e==="mixed"?this.type:e,r,c,d)}if(arguments.length===3){l=""+l,u=""+u;let c=this._nodes.get(l);if(!c)throw new W(`Graph.${i}:  could not find the "${l}" source node in the graph.`);if(!this._nodes.has(u))throw new W(`Graph.${i}:  could not find the "${u}" target node in the graph.`);return Gn(!0,e,this.multi,r,c,u,d)}throw new O(`Graph.${i}: too many arguments (expecting 1, 2 or 3 and got ${arguments.length}).`)};let o="some"+t[0].toUpperCase()+t.slice(1,-1);a.prototype[o]=function(){let l=Array.prototype.slice.call(arguments),u=l.pop();return l.push((c,f,h,g,m,p,v)=>u(c,f,h,g,m,p,v)),!!this[i].apply(this,l)};let s="every"+t[0].toUpperCase()+t.slice(1,-1);a.prototype[s]=function(){let l=Array.prototype.slice.call(arguments),u=l.pop();return l.push((c,f,h,g,m,p,v)=>!u(c,f,h,g,m,p,v)),!this[i].apply(this,l)}}function Yo(a,n){let{name:t,type:e,direction:r}=n,i=t.slice(0,-1)+"Entries";a.prototype[i]=function(o,s){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return Qe();if(!arguments.length)return Oo(this,e);if(arguments.length===1){o=""+o;let l=this._nodes.get(o);if(!l)throw new W(`Graph.${i}: could not find the "${o}" node in the graph.`);return Ho(e,r,l)}if(arguments.length===2){o=""+o,s=""+s;let l=this._nodes.get(o);if(!l)throw new W(`Graph.${i}:  could not find the "${o}" source node in the graph.`);if(!this._nodes.has(s))throw new W(`Graph.${i}:  could not find the "${s}" target node in the graph.`);return Vo(e,r,l,s)}throw new O(`Graph.${i}: too many arguments (expecting 0, 1 or 2 and got ${arguments.length}).`)}}function Ko(a){No.forEach(n=>{Xo(a,n),jo(a,n),qo(a,n),Yo(a,n)})}var Zo=[{name:"neighbors",type:"mixed"},{name:"inNeighbors",type:"directed",direction:"in"},{name:"outNeighbors",type:"directed",direction:"out"},{name:"inboundNeighbors",type:"mixed",direction:"in"},{name:"outboundNeighbors",type:"mixed",direction:"out"},{name:"directedNeighbors",type:"directed"},{name:"undirectedNeighbors",type:"undirected"}];function Yt(){this.A=null,this.B=null}Yt.prototype.wrap=function(a){this.A===null?this.A=a:this.B===null&&(this.B=a)};Yt.prototype.has=function(a){return this.A!==null&&a in this.A||this.B!==null&&a in this.B};function xt(a,n,t,e,r){for(let i in e){let o=e[i],s=o.source,l=o.target,u=s===t?l:s;if(n&&n.has(u.key))continue;let d=r(u.key,u.attributes);if(a&&d)return u.key}}function zn(a,n,t,e,r){if(n!=="mixed"){if(n==="undirected")return xt(a,null,e,e.undirected,r);if(typeof t=="string")return xt(a,null,e,e[t],r)}let i=new Yt,o;if(n!=="undirected"){if(t!=="out"){if(o=xt(a,null,e,e.in,r),a&&o)return o;i.wrap(e.in)}if(t!=="in"){if(o=xt(a,i,e,e.out,r),a&&o)return o;i.wrap(e.out)}}if(n!=="directed"&&(o=xt(a,i,e,e.undirected,r),a&&o))return o}function Qo(a,n,t){if(a!=="mixed"){if(a==="undirected")return Object.keys(t.undirected);if(typeof n=="string")return Object.keys(t[n])}let e=[];return zn(!1,a,n,t,function(r){e.push(r)}),e}function _t(a,n,t){let e=Object.keys(t),r=e.length,i=0;return{[Symbol.iterator](){return this},next(){let o=null;do{if(i>=r)return a&&a.wrap(t),{done:!0};let s=t[e[i++]],l=s.source,u=s.target;if(o=l===n?u:l,a&&a.has(o.key)){o=null;continue}}while(o===null);return{done:!1,value:{neighbor:o.key,attributes:o.attributes}}}}}function Jo(a,n,t){if(a!=="mixed"){if(a==="undirected")return _t(null,t,t.undirected);if(typeof n=="string")return _t(null,t,t[n])}let e=Qe(),r=new Yt;return a!=="undirected"&&(n!=="out"&&(e=Ae(e,_t(r,t,t.in))),n!=="in"&&(e=Ae(e,_t(r,t,t.out)))),a!=="directed"&&(e=Ae(e,_t(r,t,t.undirected))),e}function es(a,n){let{name:t,type:e,direction:r}=n;a.prototype[t]=function(i){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return[];i=""+i;let o=this._nodes.get(i);if(typeof o>"u")throw new W(`Graph.${t}: could not find the "${i}" node in the graph.`);return Qo(e==="mixed"?this.type:e,r,o)}}function ts(a,n){let{name:t,type:e,direction:r}=n,i="forEach"+t[0].toUpperCase()+t.slice(1,-1);a.prototype[i]=function(u,d){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return;u=""+u;let c=this._nodes.get(u);if(typeof c>"u")throw new W(`Graph.${i}: could not find the "${u}" node in the graph.`);zn(!1,e==="mixed"?this.type:e,r,c,d)};let o="map"+t[0].toUpperCase()+t.slice(1);a.prototype[o]=function(u,d){let c=[];return this[i](u,(f,h)=>{c.push(d(f,h))}),c};let s="filter"+t[0].toUpperCase()+t.slice(1);a.prototype[s]=function(u,d){let c=[];return this[i](u,(f,h)=>{d(f,h)&&c.push(f)}),c};let l="reduce"+t[0].toUpperCase()+t.slice(1);a.prototype[l]=function(u,d,c){if(arguments.length<3)throw new O(`Graph.${l}: missing initial value. You must provide it because the callback takes more than one argument and we cannot infer the initial value from the first iteration, as you could with a simple array.`);let f=c;return this[i](u,(h,g)=>{f=d(f,h,g)}),f}}function ns(a,n){let{name:t,type:e,direction:r}=n,i=t[0].toUpperCase()+t.slice(1,-1),o="find"+i;a.prototype[o]=function(u,d){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return;u=""+u;let c=this._nodes.get(u);if(typeof c>"u")throw new W(`Graph.${o}: could not find the "${u}" node in the graph.`);return zn(!0,e==="mixed"?this.type:e,r,c,d)};let s="some"+i;a.prototype[s]=function(u,d){return!!this[o](u,d)};let l="every"+i;a.prototype[l]=function(u,d){return!this[o](u,(f,h)=>!d(f,h))}}function as(a,n){let{name:t,type:e,direction:r}=n,i=t.slice(0,-1)+"Entries";a.prototype[i]=function(o){if(e!=="mixed"&&this.type!=="mixed"&&e!==this.type)return Qe();o=""+o;let s=this._nodes.get(o);if(typeof s>"u")throw new W(`Graph.${i}: could not find the "${o}" node in the graph.`);return Jo(e==="mixed"?this.type:e,r,s)}}function rs(a){Zo.forEach(n=>{es(a,n),ts(a,n),ns(a,n),as(a,n)})}function Ht(a,n,t,e,r){let i=e._nodes.values(),o=e.type,s,l,u,d,c,f,h;for(;s=i.next(),s.done!==!0;){let g=!1;if(l=s.value,o!=="undirected"){d=l.out;for(u in d){c=d[u];do{if(f=c.target,g=!0,h=r(l.key,f.key,l.attributes,f.attributes,c.key,c.attributes,c.undirected),a&&h)return c;c=c.next}while(c)}}if(o!=="directed"){d=l.undirected;for(u in d)if(!(n&&l.key>u)){c=d[u];do{if(f=c.target,f.key!==u&&(f=c.source),g=!0,h=r(l.key,f.key,l.attributes,f.attributes,c.key,c.attributes,c.undirected),a&&h)return c;c=c.next}while(c)}}if(t&&!g&&(h=r(l.key,null,l.attributes,null,null,null,null),a&&h))return null}}function is(a,n){let t={key:a};return Ua(n.attributes)||(t.attributes=re({},n.attributes)),t}function os(a,n,t){let e={key:n,source:t.source.key,target:t.target.key};return Ua(t.attributes)||(e.attributes=re({},t.attributes)),a==="mixed"&&t.undirected&&(e.undirected=!0),e}function ss(a){if(!oe(a))throw new O('Graph.import: invalid serialized node. A serialized node should be a plain object with at least a "key" property.');if(!("key"in a))throw new O("Graph.import: serialized node is missing its key.");if("attributes"in a&&(!oe(a.attributes)||a.attributes===null))throw new O("Graph.import: invalid attributes. Attributes should be a plain object, null or omitted.")}function ls(a){if(!oe(a))throw new O('Graph.import: invalid serialized edge. A serialized edge should be a plain object with at least a "source" & "target" property.');if(!("source"in a))throw new O("Graph.import: serialized edge is missing its source.");if(!("target"in a))throw new O("Graph.import: serialized edge is missing its target.");if("attributes"in a&&(!oe(a.attributes)||a.attributes===null))throw new O("Graph.import: invalid attributes. Attributes should be a plain object, null or omitted.");if("undirected"in a&&typeof a.undirected!="boolean")throw new O("Graph.import: invalid undirectedness information. Undirected should be boolean or omitted.")}var us=co(),ds=new Set(["directed","undirected","mixed"]),Ba=new Set(["domain","_events","_eventsCount","_maxListeners"]),cs=[{name:a=>`${a}Edge`,generateKey:!0},{name:a=>`${a}DirectedEdge`,generateKey:!0,type:"directed"},{name:a=>`${a}UndirectedEdge`,generateKey:!0,type:"undirected"},{name:a=>`${a}EdgeWithKey`},{name:a=>`${a}DirectedEdgeWithKey`,type:"directed"},{name:a=>`${a}UndirectedEdgeWithKey`,type:"undirected"}],hs={allowSelfLoops:!0,multi:!1,type:"mixed"};function fs(a,n,t){if(t&&!oe(t))throw new O(`Graph.addNode: invalid attributes. Expecting an object but got "${t}"`);if(n=""+n,t=t||{},a._nodes.has(n))throw new V(`Graph.addNode: the "${n}" node already exist in the graph.`);let e=new a.NodeDataClass(n,t);return a._nodes.set(n,e),a.emit("nodeAdded",{key:n,attributes:t}),e}function Wa(a,n,t){let e=new a.NodeDataClass(n,t);return a._nodes.set(n,e),a.emit("nodeAdded",{key:n,attributes:t}),e}function Ka(a,n,t,e,r,i,o,s){if(!e&&a.type==="undirected")throw new V(`Graph.${n}: you cannot add a directed edge to an undirected graph. Use the #.addEdge or #.addUndirectedEdge instead.`);if(e&&a.type==="directed")throw new V(`Graph.${n}: you cannot add an undirected edge to a directed graph. Use the #.addEdge or #.addDirectedEdge instead.`);if(s&&!oe(s))throw new O(`Graph.${n}: invalid attributes. Expecting an object but got "${s}"`);if(i=""+i,o=""+o,s=s||{},!a.allowSelfLoops&&i===o)throw new V(`Graph.${n}: source & target are the same ("${i}"), thus creating a loop explicitly forbidden by this graph 'allowSelfLoops' option set to false.`);let l=a._nodes.get(i),u=a._nodes.get(o);if(!l)throw new W(`Graph.${n}: source node "${i}" not found.`);if(!u)throw new W(`Graph.${n}: target node "${o}" not found.`);let d={key:null,undirected:e,source:i,target:o,attributes:s};if(t)r=a._edgeKeyGenerator();else if(r=""+r,a._edges.has(r))throw new V(`Graph.${n}: the "${r}" edge already exists in the graph.`);if(!a.multi&&(e?typeof l.undirected[o]<"u":typeof l.out[o]<"u"))throw new V(`Graph.${n}: an edge linking "${i}" to "${o}" already exists. If you really want to add multiple edges linking those nodes, you should create a multi graph by using the 'multi' option.`);let c=new Je(e,r,l,u,s);a._edges.set(r,c);let f=i===o;return e?(l.undirectedDegree++,u.undirectedDegree++,f&&(l.undirectedLoops++,a._undirectedSelfLoopCount++)):(l.outDegree++,u.inDegree++,f&&(l.directedLoops++,a._directedSelfLoopCount++)),a.multi?c.attachMulti():c.attach(),e?a._undirectedSize++:a._directedSize++,d.key=r,a.emit("edgeAdded",d),r}function gs(a,n,t,e,r,i,o,s,l){if(!e&&a.type==="undirected")throw new V(`Graph.${n}: you cannot merge/update a directed edge to an undirected graph. Use the #.mergeEdge/#.updateEdge or #.addUndirectedEdge instead.`);if(e&&a.type==="directed")throw new V(`Graph.${n}: you cannot merge/update an undirected edge to a directed graph. Use the #.mergeEdge/#.updateEdge or #.addDirectedEdge instead.`);if(s){if(l){if(typeof s!="function")throw new O(`Graph.${n}: invalid updater function. Expecting a function but got "${s}"`)}else if(!oe(s))throw new O(`Graph.${n}: invalid attributes. Expecting an object but got "${s}"`)}i=""+i,o=""+o;let u;if(l&&(u=s,s=void 0),!a.allowSelfLoops&&i===o)throw new V(`Graph.${n}: source & target are the same ("${i}"), thus creating a loop explicitly forbidden by this graph 'allowSelfLoops' option set to false.`);let d=a._nodes.get(i),c=a._nodes.get(o),f,h;if(!t&&(f=a._edges.get(r),f)){if((f.source.key!==i||f.target.key!==o)&&(!e||f.source.key!==o||f.target.key!==i))throw new V(`Graph.${n}: inconsistency detected when attempting to merge the "${r}" edge with "${i}" source & "${o}" target vs. ("${f.source.key}", "${f.target.key}").`);h=f}if(!h&&!a.multi&&d&&(h=e?d.undirected[o]:d.out[o]),h){let b=[h.key,!1,!1,!1];if(l?!u:!s)return b;if(l){let y=h.attributes;h.attributes=u(y),a.emit("edgeAttributesUpdated",{type:"replace",key:h.key,attributes:h.attributes})}else re(h.attributes,s),a.emit("edgeAttributesUpdated",{type:"merge",key:h.key,attributes:h.attributes,data:s});return b}s=s||{},l&&u&&(s=u(s));let g={key:null,undirected:e,source:i,target:o,attributes:s};if(t)r=a._edgeKeyGenerator();else if(r=""+r,a._edges.has(r))throw new V(`Graph.${n}: the "${r}" edge already exists in the graph.`);let m=!1,p=!1;d||(d=Wa(a,i,{}),m=!0,i===o&&(c=d,p=!0)),c||(c=Wa(a,o,{}),p=!0),f=new Je(e,r,d,c,s),a._edges.set(r,f);let v=i===o;return e?(d.undirectedDegree++,c.undirectedDegree++,v&&(d.undirectedLoops++,a._undirectedSelfLoopCount++)):(d.outDegree++,c.inDegree++,v&&(d.directedLoops++,a._directedSelfLoopCount++)),a.multi?f.attachMulti():f.attach(),e?a._undirectedSize++:a._directedSize++,g.key=r,a.emit("edgeAdded",g),[r,!0,m,p]}function Ze(a,n){a._edges.delete(n.key);let{source:t,target:e,attributes:r}=n,i=n.undirected,o=t===e;i?(t.undirectedDegree--,e.undirectedDegree--,o&&(t.undirectedLoops--,a._undirectedSelfLoopCount--)):(t.outDegree--,e.inDegree--,o&&(t.directedLoops--,a._directedSelfLoopCount--)),a.multi?n.detachMulti():n.detach(),i?a._undirectedSize--:a._directedSize--,a.emit("edgeDropped",{key:n.key,attributes:r,source:t.key,target:e.key,undirected:i})}var ee=class a extends Oa.EventEmitter{constructor(n){if(super(),n=re({},hs,n),typeof n.multi!="boolean")throw new O(`Graph.constructor: invalid 'multi' option. Expecting a boolean but got "${n.multi}".`);if(!ds.has(n.type))throw new O(`Graph.constructor: invalid 'type' option. Should be one of "mixed", "directed" or "undirected" but got "${n.type}".`);if(typeof n.allowSelfLoops!="boolean")throw new O(`Graph.constructor: invalid 'allowSelfLoops' option. Expecting a boolean but got "${n.allowSelfLoops}".`);let t=n.type==="mixed"?Ha:n.type==="directed"?$a:Va;he(this,"NodeDataClass",t);let e="geid_"+us()+"_",r=0,i=()=>{let o;do o=e+r++;while(this._edges.has(o));return o};he(this,"_attributes",{}),he(this,"_nodes",new Map),he(this,"_edges",new Map),he(this,"_directedSize",0),he(this,"_undirectedSize",0),he(this,"_directedSelfLoopCount",0),he(this,"_undirectedSelfLoopCount",0),he(this,"_edgeKeyGenerator",i),he(this,"_options",n),Ba.forEach(o=>he(this,o,this[o])),ye(this,"order",()=>this._nodes.size),ye(this,"size",()=>this._edges.size),ye(this,"directedSize",()=>this._directedSize),ye(this,"undirectedSize",()=>this._undirectedSize),ye(this,"selfLoopCount",()=>this._directedSelfLoopCount+this._undirectedSelfLoopCount),ye(this,"directedSelfLoopCount",()=>this._directedSelfLoopCount),ye(this,"undirectedSelfLoopCount",()=>this._undirectedSelfLoopCount),ye(this,"multi",this._options.multi),ye(this,"type",this._options.type),ye(this,"allowSelfLoops",this._options.allowSelfLoops),ye(this,"implementation",()=>"graphology")}_resetInstanceCounters(){this._directedSize=0,this._undirectedSize=0,this._directedSelfLoopCount=0,this._undirectedSelfLoopCount=0}hasNode(n){return this._nodes.has(""+n)}hasDirectedEdge(n,t){if(this.type==="undirected")return!1;if(arguments.length===1){let e=""+n,r=this._edges.get(e);return!!r&&!r.undirected}else if(arguments.length===2){n=""+n,t=""+t;let e=this._nodes.get(n);return e?e.out.hasOwnProperty(t):!1}throw new O(`Graph.hasDirectedEdge: invalid arity (${arguments.length}, instead of 1 or 2). You can either ask for an edge id or for the existence of an edge between a source & a target.`)}hasUndirectedEdge(n,t){if(this.type==="directed")return!1;if(arguments.length===1){let e=""+n,r=this._edges.get(e);return!!r&&r.undirected}else if(arguments.length===2){n=""+n,t=""+t;let e=this._nodes.get(n);return e?e.undirected.hasOwnProperty(t):!1}throw new O(`Graph.hasDirectedEdge: invalid arity (${arguments.length}, instead of 1 or 2). You can either ask for an edge id or for the existence of an edge between a source & a target.`)}hasEdge(n,t){if(arguments.length===1){let e=""+n;return this._edges.has(e)}else if(arguments.length===2){n=""+n,t=""+t;let e=this._nodes.get(n);return e?typeof e.out<"u"&&e.out.hasOwnProperty(t)||typeof e.undirected<"u"&&e.undirected.hasOwnProperty(t):!1}throw new O(`Graph.hasEdge: invalid arity (${arguments.length}, instead of 1 or 2). You can either ask for an edge id or for the existence of an edge between a source & a target.`)}directedEdge(n,t){if(this.type==="undirected")return;if(n=""+n,t=""+t,this.multi)throw new V("Graph.directedEdge: this method is irrelevant with multigraphs since there might be multiple edges between source & target. See #.directedEdges instead.");let e=this._nodes.get(n);if(!e)throw new W(`Graph.directedEdge: could not find the "${n}" source node in the graph.`);if(!this._nodes.has(t))throw new W(`Graph.directedEdge: could not find the "${t}" target node in the graph.`);let r=e.out&&e.out[t]||void 0;if(r)return r.key}undirectedEdge(n,t){if(this.type==="directed")return;if(n=""+n,t=""+t,this.multi)throw new V("Graph.undirectedEdge: this method is irrelevant with multigraphs since there might be multiple edges between source & target. See #.undirectedEdges instead.");let e=this._nodes.get(n);if(!e)throw new W(`Graph.undirectedEdge: could not find the "${n}" source node in the graph.`);if(!this._nodes.has(t))throw new W(`Graph.undirectedEdge: could not find the "${t}" target node in the graph.`);let r=e.undirected&&e.undirected[t]||void 0;if(r)return r.key}edge(n,t){if(this.multi)throw new V("Graph.edge: this method is irrelevant with multigraphs since there might be multiple edges between source & target. See #.edges instead.");n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.edge: could not find the "${n}" source node in the graph.`);if(!this._nodes.has(t))throw new W(`Graph.edge: could not find the "${t}" target node in the graph.`);let r=e.out&&e.out[t]||e.undirected&&e.undirected[t]||void 0;if(r)return r.key}areDirectedNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areDirectedNeighbors: could not find the "${n}" node in the graph.`);return this.type==="undirected"?!1:t in e.in||t in e.out}areOutNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areOutNeighbors: could not find the "${n}" node in the graph.`);return this.type==="undirected"?!1:t in e.out}areInNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areInNeighbors: could not find the "${n}" node in the graph.`);return this.type==="undirected"?!1:t in e.in}areUndirectedNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areUndirectedNeighbors: could not find the "${n}" node in the graph.`);return this.type==="directed"?!1:t in e.undirected}areNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areNeighbors: could not find the "${n}" node in the graph.`);return this.type!=="undirected"&&(t in e.in||t in e.out)||this.type!=="directed"&&t in e.undirected}areInboundNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areInboundNeighbors: could not find the "${n}" node in the graph.`);return this.type!=="undirected"&&t in e.in||this.type!=="directed"&&t in e.undirected}areOutboundNeighbors(n,t){n=""+n,t=""+t;let e=this._nodes.get(n);if(!e)throw new W(`Graph.areOutboundNeighbors: could not find the "${n}" node in the graph.`);return this.type!=="undirected"&&t in e.out||this.type!=="directed"&&t in e.undirected}inDegree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.inDegree: could not find the "${n}" node in the graph.`);return this.type==="undirected"?0:t.inDegree}outDegree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.outDegree: could not find the "${n}" node in the graph.`);return this.type==="undirected"?0:t.outDegree}directedDegree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.directedDegree: could not find the "${n}" node in the graph.`);return this.type==="undirected"?0:t.inDegree+t.outDegree}undirectedDegree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.undirectedDegree: could not find the "${n}" node in the graph.`);return this.type==="directed"?0:t.undirectedDegree}inboundDegree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.inboundDegree: could not find the "${n}" node in the graph.`);let e=0;return this.type!=="directed"&&(e+=t.undirectedDegree),this.type!=="undirected"&&(e+=t.inDegree),e}outboundDegree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.outboundDegree: could not find the "${n}" node in the graph.`);let e=0;return this.type!=="directed"&&(e+=t.undirectedDegree),this.type!=="undirected"&&(e+=t.outDegree),e}degree(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.degree: could not find the "${n}" node in the graph.`);let e=0;return this.type!=="directed"&&(e+=t.undirectedDegree),this.type!=="undirected"&&(e+=t.inDegree+t.outDegree),e}inDegreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.inDegreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);return this.type==="undirected"?0:t.inDegree-t.directedLoops}outDegreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.outDegreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);return this.type==="undirected"?0:t.outDegree-t.directedLoops}directedDegreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.directedDegreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);return this.type==="undirected"?0:t.inDegree+t.outDegree-t.directedLoops*2}undirectedDegreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.undirectedDegreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);return this.type==="directed"?0:t.undirectedDegree-t.undirectedLoops*2}inboundDegreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.inboundDegreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);let e=0,r=0;return this.type!=="directed"&&(e+=t.undirectedDegree,r+=t.undirectedLoops*2),this.type!=="undirected"&&(e+=t.inDegree,r+=t.directedLoops),e-r}outboundDegreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.outboundDegreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);let e=0,r=0;return this.type!=="directed"&&(e+=t.undirectedDegree,r+=t.undirectedLoops*2),this.type!=="undirected"&&(e+=t.outDegree,r+=t.directedLoops),e-r}degreeWithoutSelfLoops(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.degreeWithoutSelfLoops: could not find the "${n}" node in the graph.`);let e=0,r=0;return this.type!=="directed"&&(e+=t.undirectedDegree,r+=t.undirectedLoops*2),this.type!=="undirected"&&(e+=t.inDegree+t.outDegree,r+=t.directedLoops*2),e-r}source(n){n=""+n;let t=this._edges.get(n);if(!t)throw new W(`Graph.source: could not find the "${n}" edge in the graph.`);return t.source.key}target(n){n=""+n;let t=this._edges.get(n);if(!t)throw new W(`Graph.target: could not find the "${n}" edge in the graph.`);return t.target.key}extremities(n){n=""+n;let t=this._edges.get(n);if(!t)throw new W(`Graph.extremities: could not find the "${n}" edge in the graph.`);return[t.source.key,t.target.key]}opposite(n,t){n=""+n,t=""+t;let e=this._edges.get(t);if(!e)throw new W(`Graph.opposite: could not find the "${t}" edge in the graph.`);let r=e.source.key,i=e.target.key;if(n===r)return i;if(n===i)return r;throw new W(`Graph.opposite: the "${n}" node is not attached to the "${t}" edge (${r}, ${i}).`)}hasExtremity(n,t){n=""+n,t=""+t;let e=this._edges.get(n);if(!e)throw new W(`Graph.hasExtremity: could not find the "${n}" edge in the graph.`);return e.source.key===t||e.target.key===t}isUndirected(n){n=""+n;let t=this._edges.get(n);if(!t)throw new W(`Graph.isUndirected: could not find the "${n}" edge in the graph.`);return t.undirected}isDirected(n){n=""+n;let t=this._edges.get(n);if(!t)throw new W(`Graph.isDirected: could not find the "${n}" edge in the graph.`);return!t.undirected}isSelfLoop(n){n=""+n;let t=this._edges.get(n);if(!t)throw new W(`Graph.isSelfLoop: could not find the "${n}" edge in the graph.`);return t.source===t.target}addNode(n,t){return fs(this,n,t).key}mergeNode(n,t){if(t&&!oe(t))throw new O(`Graph.mergeNode: invalid attributes. Expecting an object but got "${t}"`);n=""+n,t=t||{};let e=this._nodes.get(n);return e?(t&&(re(e.attributes,t),this.emit("nodeAttributesUpdated",{type:"merge",key:n,attributes:e.attributes,data:t})),[n,!1]):(e=new this.NodeDataClass(n,t),this._nodes.set(n,e),this.emit("nodeAdded",{key:n,attributes:t}),[n,!0])}updateNode(n,t){if(t&&typeof t!="function")throw new O(`Graph.updateNode: invalid updater function. Expecting a function but got "${t}"`);n=""+n;let e=this._nodes.get(n);if(e){if(t){let i=e.attributes;e.attributes=t(i),this.emit("nodeAttributesUpdated",{type:"replace",key:n,attributes:e.attributes})}return[n,!1]}let r=t?t({}):{};return e=new this.NodeDataClass(n,r),this._nodes.set(n,e),this.emit("nodeAdded",{key:n,attributes:r}),[n,!0]}dropNode(n){n=""+n;let t=this._nodes.get(n);if(!t)throw new W(`Graph.dropNode: could not find the "${n}" node in the graph.`);let e;if(this.type!=="undirected"){for(let r in t.out){e=t.out[r];do Ze(this,e),e=e.next;while(e)}for(let r in t.in){e=t.in[r];do Ze(this,e),e=e.next;while(e)}}if(this.type!=="directed")for(let r in t.undirected){e=t.undirected[r];do Ze(this,e),e=e.next;while(e)}this._nodes.delete(n),this.emit("nodeDropped",{key:n,attributes:t.attributes})}dropEdge(n){let t;if(arguments.length>1){let e=""+arguments[0],r=""+arguments[1];if(t=fe(this,e,r,this.type),!t)throw new W(`Graph.dropEdge: could not find the "${e}" -> "${r}" edge in the graph.`)}else if(n=""+n,t=this._edges.get(n),!t)throw new W(`Graph.dropEdge: could not find the "${n}" edge in the graph.`);return Ze(this,t),this}dropDirectedEdge(n,t){if(arguments.length<2)throw new V("Graph.dropDirectedEdge: it does not make sense to try and drop a directed edge by key. What if the edge with this key is undirected? Use #.dropEdge for this purpose instead.");if(this.multi)throw new V("Graph.dropDirectedEdge: cannot use a {source,target} combo when dropping an edge in a MultiGraph since we cannot infer the one you want to delete as there could be multiple ones.");n=""+n,t=""+t;let e=fe(this,n,t,"directed");if(!e)throw new W(`Graph.dropDirectedEdge: could not find a "${n}" -> "${t}" edge in the graph.`);return Ze(this,e),this}dropUndirectedEdge(n,t){if(arguments.length<2)throw new V("Graph.dropUndirectedEdge: it does not make sense to drop a directed edge by key. What if the edge with this key is undirected? Use #.dropEdge for this purpose instead.");if(this.multi)throw new V("Graph.dropUndirectedEdge: cannot use a {source,target} combo when dropping an edge in a MultiGraph since we cannot infer the one you want to delete as there could be multiple ones.");let e=fe(this,n,t,"undirected");if(!e)throw new W(`Graph.dropUndirectedEdge: could not find a "${n}" -> "${t}" edge in the graph.`);return Ze(this,e),this}clear(){this._edges.clear(),this._nodes.clear(),this._resetInstanceCounters(),this.emit("cleared")}clearEdges(){let n=this._nodes.values(),t;for(;t=n.next(),t.done!==!0;)t.value.clear();this._edges.clear(),this._resetInstanceCounters(),this.emit("edgesCleared")}getAttribute(n){return this._attributes[n]}getAttributes(){return this._attributes}hasAttribute(n){return this._attributes.hasOwnProperty(n)}setAttribute(n,t){return this._attributes[n]=t,this.emit("attributesUpdated",{type:"set",attributes:this._attributes,name:n}),this}updateAttribute(n,t){if(typeof t!="function")throw new O("Graph.updateAttribute: updater should be a function.");let e=this._attributes[n];return this._attributes[n]=t(e),this.emit("attributesUpdated",{type:"set",attributes:this._attributes,name:n}),this}removeAttribute(n){return delete this._attributes[n],this.emit("attributesUpdated",{type:"remove",attributes:this._attributes,name:n}),this}replaceAttributes(n){if(!oe(n))throw new O("Graph.replaceAttributes: provided attributes are not a plain object.");return this._attributes=n,this.emit("attributesUpdated",{type:"replace",attributes:this._attributes}),this}mergeAttributes(n){if(!oe(n))throw new O("Graph.mergeAttributes: provided attributes are not a plain object.");return re(this._attributes,n),this.emit("attributesUpdated",{type:"merge",attributes:this._attributes,data:n}),this}updateAttributes(n){if(typeof n!="function")throw new O("Graph.updateAttributes: provided updater is not a function.");return this._attributes=n(this._attributes),this.emit("attributesUpdated",{type:"update",attributes:this._attributes}),this}updateEachNodeAttributes(n,t){if(typeof n!="function")throw new O("Graph.updateEachNodeAttributes: expecting an updater function.");if(t&&!Ma(t))throw new O("Graph.updateEachNodeAttributes: invalid hints. Expecting an object having the following shape: {attributes?: [string]}");let e=this._nodes.values(),r,i;for(;r=e.next(),r.done!==!0;)i=r.value,i.attributes=n(i.key,i.attributes);this.emit("eachNodeAttributesUpdated",{hints:t||null})}updateEachEdgeAttributes(n,t){if(typeof n!="function")throw new O("Graph.updateEachEdgeAttributes: expecting an updater function.");if(t&&!Ma(t))throw new O("Graph.updateEachEdgeAttributes: invalid hints. Expecting an object having the following shape: {attributes?: [string]}");let e=this._edges.values(),r,i,o,s;for(;r=e.next(),r.done!==!0;)i=r.value,o=i.source,s=i.target,i.attributes=n(i.key,i.attributes,o.key,s.key,o.attributes,s.attributes,i.undirected);this.emit("eachEdgeAttributesUpdated",{hints:t||null})}forEachAdjacencyEntry(n){if(typeof n!="function")throw new O("Graph.forEachAdjacencyEntry: expecting a callback.");Ht(!1,!1,!1,this,n)}forEachAdjacencyEntryWithOrphans(n){if(typeof n!="function")throw new O("Graph.forEachAdjacencyEntryWithOrphans: expecting a callback.");Ht(!1,!1,!0,this,n)}forEachAssymetricAdjacencyEntry(n){if(typeof n!="function")throw new O("Graph.forEachAssymetricAdjacencyEntry: expecting a callback.");Ht(!1,!0,!1,this,n)}forEachAssymetricAdjacencyEntryWithOrphans(n){if(typeof n!="function")throw new O("Graph.forEachAssymetricAdjacencyEntryWithOrphans: expecting a callback.");Ht(!1,!0,!0,this,n)}nodes(){return Array.from(this._nodes.keys())}forEachNode(n){if(typeof n!="function")throw new O("Graph.forEachNode: expecting a callback.");let t=this._nodes.values(),e,r;for(;e=t.next(),e.done!==!0;)r=e.value,n(r.key,r.attributes)}findNode(n){if(typeof n!="function")throw new O("Graph.findNode: expecting a callback.");let t=this._nodes.values(),e,r;for(;e=t.next(),e.done!==!0;)if(r=e.value,n(r.key,r.attributes))return r.key}mapNodes(n){if(typeof n!="function")throw new O("Graph.mapNode: expecting a callback.");let t=this._nodes.values(),e,r,i=new Array(this.order),o=0;for(;e=t.next(),e.done!==!0;)r=e.value,i[o++]=n(r.key,r.attributes);return i}someNode(n){if(typeof n!="function")throw new O("Graph.someNode: expecting a callback.");let t=this._nodes.values(),e,r;for(;e=t.next(),e.done!==!0;)if(r=e.value,n(r.key,r.attributes))return!0;return!1}everyNode(n){if(typeof n!="function")throw new O("Graph.everyNode: expecting a callback.");let t=this._nodes.values(),e,r;for(;e=t.next(),e.done!==!0;)if(r=e.value,!n(r.key,r.attributes))return!1;return!0}filterNodes(n){if(typeof n!="function")throw new O("Graph.filterNodes: expecting a callback.");let t=this._nodes.values(),e,r,i=[];for(;e=t.next(),e.done!==!0;)r=e.value,n(r.key,r.attributes)&&i.push(r.key);return i}reduceNodes(n,t){if(typeof n!="function")throw new O("Graph.reduceNodes: expecting a callback.");if(arguments.length<2)throw new O("Graph.reduceNodes: missing initial value. You must provide it because the callback takes more than one argument and we cannot infer the initial value from the first iteration, as you could with a simple array.");let e=t,r=this._nodes.values(),i,o;for(;i=r.next(),i.done!==!0;)o=i.value,e=n(e,o.key,o.attributes);return e}nodeEntries(){let n=this._nodes.values();return{[Symbol.iterator](){return this},next(){let t=n.next();if(t.done)return t;let e=t.value;return{value:{node:e.key,attributes:e.attributes},done:!1}}}}export(){let n=new Array(this._nodes.size),t=0;this._nodes.forEach((r,i)=>{n[t++]=is(i,r)});let e=new Array(this._edges.size);return t=0,this._edges.forEach((r,i)=>{e[t++]=os(this.type,i,r)}),{options:{type:this.type,multi:this.multi,allowSelfLoops:this.allowSelfLoops},attributes:this.getAttributes(),nodes:n,edges:e}}import(n,t=!1){if(n instanceof a)return n.forEachNode((l,u)=>{t?this.mergeNode(l,u):this.addNode(l,u)}),n.forEachEdge((l,u,d,c,f,h,g)=>{t?g?this.mergeUndirectedEdgeWithKey(l,d,c,u):this.mergeDirectedEdgeWithKey(l,d,c,u):g?this.addUndirectedEdgeWithKey(l,d,c,u):this.addDirectedEdgeWithKey(l,d,c,u)}),this;if(!oe(n))throw new O("Graph.import: invalid argument. Expecting a serialized graph or, alternatively, a Graph instance.");if(n.attributes){if(!oe(n.attributes))throw new O("Graph.import: invalid attributes. Expecting a plain object.");t?this.mergeAttributes(n.attributes):this.replaceAttributes(n.attributes)}let e,r,i,o,s;if(n.nodes){if(i=n.nodes,!Array.isArray(i))throw new O("Graph.import: invalid nodes. Expecting an array.");for(e=0,r=i.length;e<r;e++){o=i[e],ss(o);let{key:l,attributes:u}=o;t?this.mergeNode(l,u):this.addNode(l,u)}}if(n.edges){let l=!1;if(this.type==="undirected"&&(l=!0),i=n.edges,!Array.isArray(i))throw new O("Graph.import: invalid edges. Expecting an array.");for(e=0,r=i.length;e<r;e++){s=i[e],ls(s);let{source:u,target:d,attributes:c,undirected:f=l}=s,h;"key"in s?(h=t?f?this.mergeUndirectedEdgeWithKey:this.mergeDirectedEdgeWithKey:f?this.addUndirectedEdgeWithKey:this.addDirectedEdgeWithKey,h.call(this,s.key,u,d,c)):(h=t?f?this.mergeUndirectedEdge:this.mergeDirectedEdge:f?this.addUndirectedEdge:this.addDirectedEdge,h.call(this,u,d,c))}}return this}nullCopy(n){let t=new a(re({},this._options,n));return t.replaceAttributes(re({},this.getAttributes())),t}emptyCopy(n){let t=this.nullCopy(n);return this._nodes.forEach((e,r)=>{let i=re({},e.attributes);e=new t.NodeDataClass(r,i),t._nodes.set(r,e)}),t}copy(n){if(n=n||{},typeof n.type=="string"&&n.type!==this.type&&n.type!=="mixed")throw new V(`Graph.copy: cannot create an incompatible copy from "${this.type}" type to "${n.type}" because this would mean losing information about the current graph.`);if(typeof n.multi=="boolean"&&n.multi!==this.multi&&n.multi!==!0)throw new V("Graph.copy: cannot create an incompatible copy by downgrading a multi graph to a simple one because this would mean losing information about the current graph.");if(typeof n.allowSelfLoops=="boolean"&&n.allowSelfLoops!==this.allowSelfLoops&&n.allowSelfLoops!==!0)throw new V("Graph.copy: cannot create an incompatible copy from a graph allowing self loops to one that does not because this would mean losing information about the current graph.");let t=this.emptyCopy(n),e=this._edges.values(),r,i;for(;r=e.next(),r.done!==!0;)i=r.value,Ka(t,"copy",!1,i.undirected,i.key,i.source.key,i.target.key,re({},i.attributes));return t}toJSON(){return this.export()}toString(){return"[object Graph]"}inspect(){let n={};this._nodes.forEach((i,o)=>{n[o]=i.attributes});let t={},e={};this._edges.forEach((i,o)=>{let s=i.undirected?"--":"->",l="",u=i.source.key,d=i.target.key,c;i.undirected&&u>d&&(c=u,u=d,d=c);let f=`(${u})${s}(${d})`;o.startsWith("geid_")?this.multi&&(typeof e[f]>"u"?e[f]=0:e[f]++,l+=`${e[f]}. `):l+=`[${o}]: `,l+=f,t[l]=i.attributes});let r={};for(let i in this)this.hasOwnProperty(i)&&!Ba.has(i)&&typeof this[i]!="function"&&typeof i!="symbol"&&(r[i]=this[i]);return r.attributes=this._attributes,r.nodes=n,r.edges=t,he(r,"constructor",this.constructor),r}};typeof Symbol<"u"&&(ee.prototype[Symbol.for("nodejs.util.inspect.custom")]=ee.prototype.inspect);cs.forEach(a=>{["add","merge","update"].forEach(n=>{let t=a.name(n),e=n==="add"?Ka:gs;a.generateKey?ee.prototype[t]=function(r,i,o){return e(this,t,!0,(a.type||this.type)==="undirected",null,r,i,o,n==="update")}:ee.prototype[t]=function(r,i,o,s){return e(this,t,!1,(a.type||this.type)==="undirected",r,i,o,s,n==="update")}})});So(ee);Io(ee);Ko(ee);rs(ee);var $t=class extends ee{constructor(n){let t=re({type:"directed"},n);if("multi"in t&&t.multi!==!1)throw new O("DirectedGraph.from: inconsistent indication that the graph should be multi in given options!");if(t.type!=="directed")throw new O('DirectedGraph.from: inconsistent "'+t.type+'" type in given options!');super(t)}},Vt=class extends ee{constructor(n){let t=re({type:"undirected"},n);if("multi"in t&&t.multi!==!1)throw new O("UndirectedGraph.from: inconsistent indication that the graph should be multi in given options!");if(t.type!=="undirected")throw new O('UndirectedGraph.from: inconsistent "'+t.type+'" type in given options!');super(t)}},Xt=class extends ee{constructor(n){let t=re({multi:!0},n);if("multi"in t&&t.multi!==!0)throw new O("MultiGraph.from: inconsistent indication that the graph should be simple in given options!");super(t)}},jt=class extends ee{constructor(n){let t=re({type:"directed",multi:!0},n);if("multi"in t&&t.multi!==!0)throw new O("MultiDirectedGraph.from: inconsistent indication that the graph should be simple in given options!");if(t.type!=="directed")throw new O('MultiDirectedGraph.from: inconsistent "'+t.type+'" type in given options!');super(t)}},qt=class extends ee{constructor(n){let t=re({type:"undirected",multi:!0},n);if("multi"in t&&t.multi!==!0)throw new O("MultiUndirectedGraph.from: inconsistent indication that the graph should be simple in given options!");if(t.type!=="undirected")throw new O('MultiUndirectedGraph.from: inconsistent "'+t.type+'" type in given options!');super(t)}};function et(a){a.from=function(n,t){let e=re({},n.options,t),r=new a(e);return r.import(n),r}}et(ee);et($t);et(Vt);et(Xt);et(jt);et(qt);ee.Graph=ee;ee.DirectedGraph=$t;ee.UndirectedGraph=Vt;ee.MultiGraph=Xt;ee.MultiDirectedGraph=jt;ee.MultiUndirectedGraph=qt;ee.InvalidArgumentsGraphError=O;ee.NotFoundGraphError=W;ee.UsageGraphError=V;function Qt(a,n){(n==null||n>a.length)&&(n=a.length);for(var t=0,e=Array(n);t<n;t++)e[t]=a[t];return e}function Jt(a,n){if(a){if(typeof a=="string")return Qt(a,n);var t={}.toString.call(a).slice(8,-1);return t==="Object"&&a.constructor&&(t=a.constructor.name),t==="Map"||t==="Set"?Array.from(a):t==="Arguments"||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t)?Qt(a,n):void 0}}function vs(a){if(Array.isArray(a))return a}function ps(a,n){var t=a==null?null:typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(t!=null){var e,r,i,o,s=[],l=!0,u=!1;try{if(i=(t=t.call(a)).next,n===0){if(Object(t)!==t)return;l=!1}else for(;!(l=(e=i.call(t)).done)&&(s.push(e.value),s.length!==n);l=!0);}catch(d){u=!0,r=d}finally{try{if(!l&&t.return!=null&&(o=t.return(),Object(o)!==o))return}finally{if(u)throw r}}return s}}function ms(){throw new TypeError(`Invalid attempt to destructure non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function Q(a,n){return vs(a)||ps(a,n)||Jt(a,n)||ms()}function M(a,n){var t=typeof Symbol<"u"&&a[Symbol.iterator]||a["@@iterator"];if(!t){if(Array.isArray(a)||(t=Jt(a))||n&&a&&typeof a.length=="number"){t&&(a=t);var e=0,r=function(){};return{s:r,n:function(){return e>=a.length?{done:!0}:{done:!1,value:a[e++]}},e:function(l){throw l},f:r}}throw new TypeError(`Invalid attempt to iterate non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}var i,o=!0,s=!1;return{s:function(){t=t.call(a)},n:function(){var l=t.next();return o=l.done,l},e:function(l){s=!0,i=l},f:function(){try{o||t.return==null||t.return()}finally{if(s)throw i}}}}function ge(){return Float32Array.of(1,0,0,0,1,0,0,0,1)}function Kt(a,n,t){return a[0]=n,a[4]=typeof t=="number"?t:n,a}function Za(a,n){var t=Math.sin(n),e=Math.cos(n);return a[0]=e,a[1]=t,a[3]=-t,a[4]=e,a}function Qa(a,n,t){return a[6]=n,a[7]=t,a}function Ce(a,n){var t=a[0],e=a[1],r=a[2],i=a[3],o=a[4],s=a[5],l=a[6],u=a[7],d=a[8],c=n[0],f=n[1],h=n[2],g=n[3],m=n[4],p=n[5],v=n[6],b=n[7],y=n[8];return a[0]=c*t+f*i+h*l,a[1]=c*e+f*o+h*u,a[2]=c*r+f*s+h*d,a[3]=g*t+m*i+p*l,a[4]=g*e+m*o+p*u,a[5]=g*r+m*s+p*d,a[6]=v*t+b*i+y*l,a[7]=v*e+b*o+y*u,a[8]=v*r+b*s+y*d,a}function Mn(a,n){var t=Math.cos(n),e=Math.sin(n);return{x:t*a.x+e*a.y,y:-e*a.x+t*a.y}}function nt(a,n){var t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:1,e=a[0],r=a[1],i=a[3],o=a[4],s=a[6],l=a[7],u=n.x,d=n.y;return{x:u*e+d*i+s*t,y:u*r+d*o+l*t}}function bs(a,n){var t=a.height/a.width,e=n.height/n.width;return t<1&&e>1||t>1&&e<1?1:Math.min(Math.max(e,1/e),Math.max(1/t,t))}function Pe(a,n,t,e,r){var i=a.angle,o=a.ratio,s=a.x,l=a.y,u=n.width,d=n.height,c=ge(),f=Math.min(u,d)-2*e,h=bs(n,t);return r?(Ce(c,Qa(ge(),s,l)),Ce(c,Kt(ge(),o)),Ce(c,Za(ge(),i)),Ce(c,Kt(ge(),u/f/2/h,d/f/2/h))):(Ce(c,Kt(ge(),2*(f/u)*h,2*(f/d)*h)),Ce(c,Za(ge(),-i)),Ce(c,Kt(ge(),1/o)),Ce(c,Qa(ge(),-s,-l))),c}function Ja(a,n,t){var e=nt(a,{x:Math.cos(n.angle),y:Math.sin(n.angle)},0),r=e.x,i=e.y;return 1/Math.sqrt(Math.pow(r,2)+Math.pow(i,2))/t.width}function Bn(a,n,t,e,r){var i=Math.floor(n/r*e),o=Math.floor(a.drawingBufferHeight/r-t/r*e);return[i,o]}var Et={black:"#000000",silver:"#C0C0C0",gray:"#808080",grey:"#808080",white:"#FFFFFF",maroon:"#800000",red:"#FF0000",purple:"#800080",fuchsia:"#FF00FF",green:"#008000",lime:"#00FF00",olive:"#808000",yellow:"#FFFF00",navy:"#000080",blue:"#0000FF",teal:"#008080",aqua:"#00FFFF",darkblue:"#00008B",mediumblue:"#0000CD",darkgreen:"#006400",darkcyan:"#008B8B",deepskyblue:"#00BFFF",darkturquoise:"#00CED1",mediumspringgreen:"#00FA9A",springgreen:"#00FF7F",cyan:"#00FFFF",midnightblue:"#191970",dodgerblue:"#1E90FF",lightseagreen:"#20B2AA",forestgreen:"#228B22",seagreen:"#2E8B57",darkslategray:"#2F4F4F",darkslategrey:"#2F4F4F",limegreen:"#32CD32",mediumseagreen:"#3CB371",turquoise:"#40E0D0",royalblue:"#4169E1",steelblue:"#4682B4",darkslateblue:"#483D8B",mediumturquoise:"#48D1CC",indigo:"#4B0082",darkolivegreen:"#556B2F",cadetblue:"#5F9EA0",cornflowerblue:"#6495ED",rebeccapurple:"#663399",mediumaquamarine:"#66CDAA",dimgray:"#696969",dimgrey:"#696969",slateblue:"#6A5ACD",olivedrab:"#6B8E23",slategray:"#708090",slategrey:"#708090",lightslategray:"#778899",lightslategrey:"#778899",mediumslateblue:"#7B68EE",lawngreen:"#7CFC00",chartreuse:"#7FFF00",aquamarine:"#7FFFD4",skyblue:"#87CEEB",lightskyblue:"#87CEFA",blueviolet:"#8A2BE2",darkred:"#8B0000",darkmagenta:"#8B008B",saddlebrown:"#8B4513",darkseagreen:"#8FBC8F",lightgreen:"#90EE90",mediumpurple:"#9370DB",darkviolet:"#9400D3",palegreen:"#98FB98",darkorchid:"#9932CC",yellowgreen:"#9ACD32",sienna:"#A0522D",brown:"#A52A2A",darkgray:"#A9A9A9",darkgrey:"#A9A9A9",lightblue:"#ADD8E6",greenyellow:"#ADFF2F",paleturquoise:"#AFEEEE",lightsteelblue:"#B0C4DE",powderblue:"#B0E0E6",firebrick:"#B22222",darkgoldenrod:"#B8860B",mediumorchid:"#BA55D3",rosybrown:"#BC8F8F",darkkhaki:"#BDB76B",mediumvioletred:"#C71585",indianred:"#CD5C5C",peru:"#CD853F",chocolate:"#D2691E",tan:"#D2B48C",lightgray:"#D3D3D3",lightgrey:"#D3D3D3",thistle:"#D8BFD8",orchid:"#DA70D6",goldenrod:"#DAA520",palevioletred:"#DB7093",crimson:"#DC143C",gainsboro:"#DCDCDC",plum:"#DDA0DD",burlywood:"#DEB887",lightcyan:"#E0FFFF",lavender:"#E6E6FA",darksalmon:"#E9967A",violet:"#EE82EE",palegoldenrod:"#EEE8AA",lightcoral:"#F08080",khaki:"#F0E68C",aliceblue:"#F0F8FF",honeydew:"#F0FFF0",azure:"#F0FFFF",sandybrown:"#F4A460",wheat:"#F5DEB3",beige:"#F5F5DC",whitesmoke:"#F5F5F5",mintcream:"#F5FFFA",ghostwhite:"#F8F8FF",salmon:"#FA8072",antiquewhite:"#FAEBD7",linen:"#FAF0E6",lightgoldenrodyellow:"#FAFAD2",oldlace:"#FDF5E6",magenta:"#FF00FF",deeppink:"#FF1493",orangered:"#FF4500",tomato:"#FF6347",hotpink:"#FF69B4",coral:"#FF7F50",darkorange:"#FF8C00",lightsalmon:"#FFA07A",orange:"#FFA500",lightpink:"#FFB6C1",pink:"#FFC0CB",gold:"#FFD700",peachpuff:"#FFDAB9",navajowhite:"#FFDEAD",moccasin:"#FFE4B5",bisque:"#FFE4C4",mistyrose:"#FFE4E1",blanchedalmond:"#FFEBCD",papayawhip:"#FFEFD5",lavenderblush:"#FFF0F5",seashell:"#FFF5EE",cornsilk:"#FFF8DC",lemonchiffon:"#FFFACD",floralwhite:"#FFFAF0",snow:"#FFFAFA",lightyellow:"#FFFFE0",ivory:"#FFFFF0"},er=new Int8Array(4),Zt=new Int32Array(er.buffer,0,1),tr=new Float32Array(er.buffer,0,1),ys=/^\s*rgba?\s*\(/,xs=/^\s*rgba?\s*\(\s*([0-9]*)\s*,\s*([0-9]*)\s*,\s*([0-9]*)(?:\s*,\s*(.*)?)?\)\s*$/;function en(a){var n=0,t=0,e=0,r=1,i=a.toLowerCase();if(i==="transparent")return{r:0,g:0,b:0,a:0};if(i in Et)return en(Et[i]);if(a[0]==="#")a.length===4?(n=parseInt(a.charAt(1)+a.charAt(1),16),t=parseInt(a.charAt(2)+a.charAt(2),16),e=parseInt(a.charAt(3)+a.charAt(3),16)):(n=parseInt(a.charAt(1)+a.charAt(2),16),t=parseInt(a.charAt(3)+a.charAt(4),16),e=parseInt(a.charAt(5)+a.charAt(6),16)),a.length===9&&(r=parseInt(a.charAt(7)+a.charAt(8),16)/255);else if(ys.test(a)){var o=a.match(xs);o&&(n=+o[1],t=+o[2],e=+o[3],o[4]&&(r=+o[4]))}return{r:n,g:t,b:e,a:r}}function nr(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!1,t=en(a),e=t.r,r=t.g,i=t.b,o=t.a;return n?[e/255*o,r/255*o,i/255*o,o]:[e/255,r/255,i/255,o]}var tt={};for(St in Et)tt[St]=ve(Et[St]),tt[Et[St]]=tt[St];var St;function _s(a,n,t,e,r){return Zt[0]=e<<24|t<<16|n<<8|a,r&&(Zt[0]=Zt[0]&4278190079),tr[0]}function ve(a){if(a=a.toLowerCase(),typeof tt[a]<"u")return tt[a];var n=en(a),t=n.r,e=n.g,r=n.b,i=n.a;i=i*255|0;var o=_s(t,e,r,i,!0);return tt[a]=o,o}function ke(a,n){tr[0]=ve(a);var t=Zt[0];n&&(t=t|16777216);var e=t&255,r=t>>8&255,i=t>>16&255,o=t>>24&255;return[e,r,i,o]}function at(a){var n=a>>>8&255,t=a>>>16&255,e=a>>>24&255,r=a&255;return(r<<24|e<<16|t<<8|n)>>>0}function Wn(a,n,t,e){return(t<<24|n<<16|a<<8|e)>>>0}function ar(a,n,t,e,r,i){var o=Bn(a,t,e,r,i),s=Q(o,2),l=s[0],u=s[1],d=new Uint8Array(4);a.bindFramebuffer(a.FRAMEBUFFER,n),a.readPixels(l,u,1,1,a.RGBA,a.UNSIGNED_BYTE,d);var c=Q(d,4),f=c[0],h=c[1],g=c[2],m=c[3];return[f,h,g,m]}function rr(a){var n=en(a),t=n.r,e=n.g,r=n.b,i=n.a,o=(t/255).toFixed(6),s=(e/255).toFixed(6),l=(r/255).toFixed(6),u=i.toFixed(6);return"vec4(".concat(o,", ").concat(s,", ").concat(l,", ").concat(u,")")}function Ts(a,n){if(typeof a!="object"||!a)return a;var t;if(typeof Symbol<"u"&&(t=a[Symbol.toPrimitive])!==void 0){var e=t.call(a,n||"default");if(typeof e!="object")return e;throw new TypeError("@@toPrimitive must return a primitive value.")}return(n==="string"?String:Number)(a)}function sr(a){var n=Ts(a,"string");return typeof n=="symbol"?n:n+""}function S(a,n,t){return(n=sr(n))in a?Object.defineProperty(a,n,{value:t,enumerable:!0,configurable:!0,writable:!0}):a[n]=t,a}function ir(a,n){var t=Object.keys(a);if(Object.getOwnPropertySymbols){var e=Object.getOwnPropertySymbols(a);n&&(e=e.filter(function(r){return Object.getOwnPropertyDescriptor(a,r).enumerable})),t.push.apply(t,e)}return t}function B(a){for(var n=1;n<arguments.length;n++){var t=arguments[n]!=null?arguments[n]:{};n%2?ir(Object(t),!0).forEach(function(e){S(a,e,t[e])}):Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(t)):ir(Object(t)).forEach(function(e){Object.defineProperty(a,e,Object.getOwnPropertyDescriptor(t,e))})}return a}function Y(a,n){if(!(a instanceof n))throw new TypeError("Cannot call a class as a function")}function or(a,n){for(var t=0;t<n.length;t++){var e=n[t];e.enumerable=e.enumerable||!1,e.configurable=!0,"value"in e&&(e.writable=!0),Object.defineProperty(a,sr(e.key),e)}}function K(a,n,t){return n&&or(a.prototype,n),t&&or(a,t),Object.defineProperty(a,"prototype",{writable:!1}),a}function Be(a){return Be=Object.setPrototypeOf?Object.getPrototypeOf.bind():function(n){return n.__proto__||Object.getPrototypeOf(n)},Be(a)}function lr(){try{var a=!Boolean.prototype.valueOf.call(Reflect.construct(Boolean,[],function(){}))}catch{}return(lr=function(){return!!a})()}function Ss(a){if(a===void 0)throw new ReferenceError("this hasn't been initialised - super() hasn't been called");return a}function Es(a,n){if(n&&(typeof n=="object"||typeof n=="function"))return n;if(n!==void 0)throw new TypeError("Derived constructors may only return object or undefined");return Ss(a)}function te(a,n,t){return n=Be(n),Es(a,lr()?Reflect.construct(n,t||[],Be(a).constructor):n.apply(a,t))}function On(a,n){return On=Object.setPrototypeOf?Object.setPrototypeOf.bind():function(t,e){return t.__proto__=e,t},On(a,n)}function ne(a,n){if(typeof n!="function"&&n!==null)throw new TypeError("Super expression must either be null or a function");a.prototype=Object.create(n&&n.prototype,{constructor:{value:a,writable:!0,configurable:!0}}),Object.defineProperty(a,"prototype",{writable:!1}),n&&On(a,n)}function Rs(a){if(Array.isArray(a))return Qt(a)}function As(a){if(typeof Symbol<"u"&&a[Symbol.iterator]!=null||a["@@iterator"]!=null)return Array.from(a)}function Ds(){throw new TypeError(`Invalid attempt to spread non-iterable instance.
In order to be iterable, non-array objects must have a [Symbol.iterator]() method.`)}function $(a){return Rs(a)||As(a)||Jt(a)||Ds()}function Z(a){"@babel/helpers - typeof";return Z=typeof Symbol=="function"&&typeof Symbol.iterator=="symbol"?function(n){return typeof n}:function(n){return n&&typeof Symbol=="function"&&n.constructor===Symbol&&n!==Symbol.prototype?"symbol":typeof n},Z(a)}function _e(a){return Z(a)==="object"&&a!==null&&"attribute"in a}function Un(){var a=`
float sdf_circle(vec2 uv, float size) {
  return length(uv) - size;
}
`;return{name:"circle",glsl:a,uniforms:[]}}function Hn(a){var n,t=WebGL2RenderingContext,e=t.UNSIGNED_BYTE,r=(n=a?.color)!==null&&n!==void 0?n:{attribute:"color"};if(!_e(r)){var i=r,o=`
vec4 layer_fill() {
  return `.concat(rr(i),`;
}
`);return{name:"fill",uniforms:[],attributes:[],glsl:o}}var s=r.attribute,l=`
vec4 layer_fill(vec4 v_fillColor) {
  return v_fillColor;
}
`;return{name:"fill",uniforms:[],attributes:[{name:"fillColor",size:4,type:e,normalized:!0,source:s}],glsl:l}}function ur(a,n){if(typeof a=="string"){var t=nr(a).map(function(u){return u.toFixed(6)}),e=Q(t,4),r=e[0],i=e[1],o=e[2],s=e[3];return{glsl:"vec4(".concat(r,", ").concat(i,", ").concat(o,", ").concat(s,")"),attributes:[],needsNodeColors:!1}}if("node"in a&&a.node)return{glsl:a.node==="source"?"v_sourceColor":"v_targetColor",attributes:[],needsNodeColors:!0};var l=a;return{glsl:"v_".concat(n),attributes:[{name:"a_".concat(n),size:4,type:WebGL2RenderingContext.UNSIGNED_BYTE,normalized:!0,source:l.attribute,defaultValue:l.default}],needsNodeColors:!1}}function Te(a){var n=a?.color;if(n===void 0){var t=`
// Plain solid color layer
vec4 layer_plain(EdgeContext ctx) {
  return v_color;
}
`;return{name:"plain",glsl:t,uniforms:[],attributes:[]}}var e=ur(n,"plainColor"),r=`
// Plain solid color layer
vec4 layer_plain(EdgeContext ctx) {
  return `.concat(e.glsl,`;
}
`);return{name:"plain",glsl:r,uniforms:[],attributes:e.attributes,needsNodeColors:e.needsNodeColors}}function Rt(){var a=`
// Position at parameter t \u2208 [0, 1]
vec2 path_straight_position(float t, vec2 source, vec2 target) {
  return mix(source, target, t);
}

// Total length of the path (analytical - more efficient than sampling)
float path_straight_length(vec2 source, vec2 target) {
  return length(target - source);
}
`;return{name:"straight",segments:1,minBodyLengthRatio:0,linearParameterization:!0,glsl:a,uniforms:[],attributes:[]}}function $n(a){var n=a??{},t=n.segments,e=t===void 0?32:t,r=`
const float LOOP_PI = 3.141592653589793;

float loopWorldRadius() {
  float nodeWorldRadius = v_sourceNodeSize * u_correctionRatio / u_sizeRatio;
  return max(v_loopRadius * nodeWorldRadius, 0.001);
}

// Cubic B\xE9zier with P0 = P3 = source.
// Control points extend outward orthogonal to the node surface at exit/entry angles.
vec2 path_loop_position(float t, vec2 source, vec2 target) {
  float R = loopWorldRadius();
  float angle = v_loopAngle + (v_loopFixedOrientation > 0.5 ? u_cameraAngle : 0.0);
  float halfSpread = v_loopSpread * 0.5;

  float exitAngle = angle - halfSpread;
  float entryAngle = angle + halfSpread;

  // Control point distance: at t=0.5 the B\xE9zier reaches 0.75 * cpDist * cos(halfSpread)
  // from source. Solve for cpDist so the loop tip reaches exactly R.
  float cpDist = R / (0.75 * cos(halfSpread));

  vec2 cp1 = source + cpDist * vec2(cos(exitAngle), sin(exitAngle));
  vec2 cp2 = source + cpDist * vec2(cos(entryAngle), sin(entryAngle));

  float u = 1.0 - t;
  vec2 d1 = cp1 - source;
  vec2 d2 = cp2 - source;
  return source + 3.0 * t * u * (u * d1 + t * d2);
}

// Approximate arc length via chord sampling
float path_loop_length(vec2 source, vec2 target) {
  float len = 0.0;
  vec2 prev = path_loop_position(0.0, source, target);
  const int STEPS = 16;
  for (int i = 1; i <= STEPS; i++) {
    float t = float(i) / float(STEPS);
    vec2 cur = path_loop_position(t, source, target);
    len += length(cur - prev);
    prev = cur;
  }
  return len;
}
`;return{name:"loop",segments:e,glsl:r,needsNodeSize:!0,uniforms:[],attributes:[{name:"loopRadius",size:1,type:WebGL2RenderingContext.FLOAT},{name:"loopAngle",size:1,type:WebGL2RenderingContext.FLOAT},{name:"loopSpread",size:1,type:WebGL2RenderingContext.FLOAT},{name:"loopFixedOrientation",size:1,type:WebGL2RenderingContext.FLOAT}],variables:{loopRadius:{type:"number",default:4},loopAngle:{type:"number",default:Math.PI/4},loopSpread:{type:"number",default:80*Math.PI/180},loopFixedOrientation:{type:"number",default:0}},spread:{variable:"loopRadius",compute:function(o){return o+4}}}}var vr=Me(Ke());function dr(a){return Z(a)==="object"&&"glsl"in a&&!("attributes"in a)}function cr(a){return Z(a)==="object"&&"glsl"in a&&!("attributes"in a)}var At={shapes:[Un()],variables:{},layers:[Hn()],label:{},backdrop:{},labelAttachments:{}},rt={paths:[Rt(),$n()],extremities:[],variables:{},layers:[Te()],defaultHead:"none",defaultTail:"none",label:{}},tn=["nodes","topNodes"],nn=["edges","topEdges"],an=[].concat(nn,tn),hr={nodes:At,edges:rt,depthLayers:$(an)};var ws=function(n){return n},Ls=function(n){return n*n},Cs=function(n){return n*(2-n)},Ps=function(n){return(n*=2)<1?.5*n*n:-.5*(--n*(n-2)-1)},ks=function(n){return n*n*n},Fs=function(n){return--n*n*n+1},Is=function(n){return(n*=2)<1?.5*n*n*n:.5*((n-=2)*n*n+2)},Ns=function(n){return n===0?0:Math.pow(2,10*(n-1))},Gs=function(n){return n===1?1:1-Math.pow(2,-10*n)},zs=function(n){return n===0?0:n===1?1:n<.5?Math.pow(2,10*(2*n-1))/2:(2-Math.pow(2,-10*(2*n-1)))/2},Vn={linear:ws,quadraticIn:Ls,quadraticOut:Cs,quadraticInOut:Ps,cubicIn:ks,cubicOut:Fs,cubicInOut:Is,exponentialIn:Ns,exponentialOut:Gs,exponentialInOut:zs};function rn(a){return a?typeof a=="function"?a:Vn[a]:Vn.linear}function jn(a){return Z(a)==="object"&&a!==null&&"attribute"in a}function pr(a){return typeof a=="function"}function mr(a){return Z(a)==="object"&&a!==null&&"when"in a&&typeof a.when=="function"&&"then"in a}function br(a){return Z(a)==="object"&&a!==null&&"whenState"in a&&"then"in a}function yr(a){return Z(a)==="object"&&a!==null&&"whenData"in a&&"then"in a}var Ms={isHovered:!1,isLabelHovered:!1,isHidden:!1,isHighlighted:!1,isDragged:!1},Bs={isHovered:!1,isLabelHovered:!1,isHidden:!1,isHighlighted:!1,parallelIndex:0,parallelCount:1},Ws={isIdle:!0,isPanning:!1,isZooming:!1,isDragging:!1,hasHovered:!1,hasHighlighted:!1};function xr(a){return B(B({},Ms),a)}function _r(a){return B(B({},Bs),a)}function qn(a){return B(B({},Ws),a)}var Os={x:{attribute:"x"},y:{attribute:"y"},size:{whenState:"isHovered",then:{attribute:"size",defaultValue:12},else:{attribute:"size",defaultValue:10}},color:{attribute:"color",defaultValue:"#666"},label:{attribute:"label"},visibility:{whenState:"isHidden",then:"hidden",else:"visible"},labelVisibility:{whenState:"isHovered",then:"visible",else:"auto"},backdropVisibility:{whenState:"isHovered",then:"visible",else:"hidden"},backdropColor:"#ffffff",backdropShadowColor:"rgba(0, 0, 0, 0.5)",backdropShadowBlur:12,backdropPadding:6},Us={size:{attribute:"size",defaultValue:1},color:{attribute:"color",defaultValue:"#ccc"},label:{attribute:"label"},visibility:{whenState:"isHidden",then:"hidden",else:"visible"}};var sn={nodes:B(B({},Os),{},{depth:{whenState:"isHovered",then:"topNodes",else:"nodes"}}),edges:B(B({},Us),{},{depth:{whenState:["isHighlighted","isHovered"],then:"topEdges",else:"edges"}})};function Hs(a){return"min"in a||"max"in a||"minValue"in a||"maxValue"in a||"easing"in a}function $s(a){return"dict"in a}function ln(a,n){return typeof a=="string"?n[a]===!0:Array.isArray(a)?a.every(function(t){return n[t]===!0}):Z(a)==="object"&&a!==null?Object.entries(a).every(function(t){var e=Q(t,2),r=e[0],i=e[1];return n[r]===i}):!1}function Vs(a,n){var t=n[a.attribute];return t===void 0?a.defaultValue:t}function Xs(a,n,t){var e,r,i,o,s=n[a.attribute];if(s===void 0)return a.defaultValue;var l=Number(s);if(isNaN(l))return a.defaultValue;if(a.min===void 0&&a.max===void 0)return l;var u=(e=a.minValue)!==null&&e!==void 0?e:l,d=(r=a.maxValue)!==null&&r!==void 0?r:l;if(d===u){var c;return(c=a.min)!==null&&c!==void 0?c:l}var f=(l-u)/(d-u);f=Math.max(0,Math.min(1,f));var h=rn(a.easing);f=h(f);var g=(i=a.min)!==null&&i!==void 0?i:0,m=(o=a.max)!==null&&o!==void 0?o:1;return g+f*(m-g)}function js(a,n){var t=n[a.attribute];if(t===void 0)return a.defaultValue;var e=String(t);return e in a.dict?a.dict[e]:a.defaultValue}function qs(a,n,t){return $s(a)?js(a,n):Hs(a)?Xs(a,n):Vs(a,n)}function Tr(a,n){return typeof a=="string"?!!n[a]:Array.isArray(a)?a.every(function(t){return!!n[t]}):Z(a)==="object"&&a!==null?Object.entries(a).every(function(t){var e=Q(t,2),r=e[0],i=e[1];return n[r]===i}):!1}function on(a,n,t,e,r,i){if(a==null)return i;if(Z(a)!=="object"&&typeof a!="function")return a;if(mr(a)){var o=a.when(n,t,e,r)?a.then:a.else;return o===void 0?i:on(o,n,t,e,r,i)}if(br(a)){var s=ln(a.whenState,t)?a.then:a.else;return s===void 0?i:on(s,n,t,e,r,i)}if(yr(a)){var l=Tr(a.whenData,n)?a.then:a.else;return l===void 0?i:on(l,n,t,e,r,i)}if(pr(a)){var u=a(n,t,e,r);return u??i}if(jn(a)){var d=qs(a,n);return d??i}return a}function xe(a){if(a==null)return"static";if(mr(a))return"graph-state";if(br(a)){var n=xe(a.then),t=a.else!==void 0?xe(a.else):"static";return pe("item-state",pe(n,t))}if(yr(a)){var e=xe(a.then),r=a.else!==void 0?xe(a.else):"static";return pe(e,r)}return pr(a)?"graph-state":(jn(a),"static")}function pe(a,n){return a==="graph-state"||n==="graph-state"?"graph-state":a==="item-state"||n==="item-state"?"item-state":"static"}function Yn(a){if(!a)return{dependency:"static",xAttribute:null,yAttribute:null};var n=Array.isArray(a)?a:[a],t="static",e=null,r=null,i=M(n),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;if("matchData"in s&&"cases"in s)for(var l=s.cases,u=0,d=Object.values(l);u<d.length;u++)for(var c=d[u],f=0,h=Object.values(c);f<h.length;f++){var g=h[f];t=pe(t,xe(g))}else if("matchState"in s&&"cases"in s){t=pe(t,"item-state");for(var m=s.cases,p=0,v=Object.values(m);p<v.length;p++)for(var b=v[p],y=0,T=Object.values(b);y<T.length;y++){var x=T[y];t=pe(t,xe(x))}}else if("when"in s&&"then"in s)t="graph-state";else if("whenState"in s){t=pe(t,"item-state");var _=s.then;if(_&&Z(_)==="object")for(var R=0,E=Object.values(_);R<E.length;R++){var L=E[R];t=pe(t,xe(L))}var D=s.else;if(D&&Z(D)==="object")for(var F=0,A=Object.values(D);F<A.length;F++){var I=A[F];t=pe(t,xe(I))}}else if("whenData"in s){var w=s.then;if(w&&Z(w)==="object")for(var k=0,G=Object.values(w);k<G.length;k++){var N=G[k];t=pe(t,xe(N))}var P=s.else;if(P&&Z(P)==="object")for(var C=0,z=Object.values(P);C<z.length;C++){var H=z[C];t=pe(t,xe(H))}}else for(var U=0,q=Object.entries(s);U<q.length;U++){var X=Q(q[U],2),j=X[0],be=X[1];if(!Zn.has(j)&&(t=pe(t,xe(be)),(j==="x"||j==="y")&&jn(be))){var le=be.attribute;j==="x"&&!e&&(e=le),j==="y"&&!r&&(r=le)}}}}catch(Re){i.e(Re)}finally{i.f()}return{dependency:t,xAttribute:e,yAttribute:r}}var we={size:10,color:"#666",opacity:1,shape:"circle",rotationAlignment:"viewport",labelRotationAlignment:"viewport",visibility:"visible",depth:"nodes",zIndex:0,label:"",labelColor:"#000",labelSize:12,labelFont:"sans-serif",labelVisibility:"auto",labelPosition:"right",labelAngle:0,labelDepth:"nodes",backdropVisibility:"hidden",backdropColor:"transparent",backdropShadowColor:"transparent",backdropShadowBlur:0,backdropPadding:0,backdropBorderColor:"transparent",backdropBorderWidth:0,backdropCornerRadius:0,backdropLabelPadding:-1,backdropArea:"both",labelAttachment:null,labelAttachmentPlacement:"below"},Kn={size:1,color:"#ccc",opacity:1,path:"straight",selfLoopPath:"loop",parallelSpread:.25,tail:"none",head:"none",visibility:"visible",depth:"edges",zIndex:0,label:"",labelColor:"#666",labelVisibility:"auto",labelDepth:"edges"},Zn=new Set(["when","whenState","whenData","then","else"]),fr=Object.keys(we),Ys=Object.values(we),gr=Object.keys(Kn),Ks=Object.values(Kn);function it(a,n,t,e,r,i,o){for(var s in n){var l;if(!Zn.has(s)){var u=(l=a[s])!==null&&l!==void 0?l:o[s];a[s]=on(n[s],t,e,r,i,u)}}"depth"in n&&!("labelDepth"in n)&&(a.labelDepth=a.depth)}function Sr(a,n,t,e,r,i,o){var s=M(n),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;if("matchData"in u&&"cases"in u){var d,c=String((d=t[u.matchData])!==null&&d!==void 0?d:""),f=u.cases;c in f&&it(a,f[c],t,e,r,i,o)}else if("matchState"in u&&"cases"in u){var h,g=String((h=e[u.matchState])!==null&&h!==void 0?h:""),m=u.cases;g in m&&it(a,m[g],t,e,r,i,o)}else if("when"in u&&"then"in u){var p=u.when;if(!p(t,e,r,i))continue;it(a,u.then,t,e,r,i,o)}else if("whenState"in u&&"then"in u){if(!ln(u.whenState,e))continue;it(a,u.then,t,e,r,i,o)}else if("whenData"in u&&"then"in u){if(!Tr(u.whenData,t))continue;it(a,u.then,t,e,r,i,o)}else it(a,u,t,e,r,i,o)}}catch(v){s.e(v)}finally{s.f()}}function Qn(a,n,t,e,r,i){for(var o=i||{},s=o,l=0,u=fr.length;l<u;l++)s[fr[l]]=Ys[l];if(s.x=void 0,s.y=void 0,s.labelBackgroundColor=void 0,s.labelBackgroundPadding=void 0,s.labelCursor=void 0,!a){var d,c,f,h,g;return s.x=(d=n.x)!==null&&d!==void 0?d:0,s.y=(c=n.y)!==null&&c!==void 0?c:0,o.size=(f=n.size)!==null&&f!==void 0?f:10,o.color=(h=n.color)!==null&&h!==void 0?h:"#666",o.label=(g=n.label)!==null&&g!==void 0?g:"",o}var m=Array.isArray(a)?a:[a];return Sr(s,m,n,t,e,r,we),o}function Jn(a,n,t,e,r,i){for(var o=i||{},s=o,l=0,u=gr.length;l<u;l++)s[gr[l]]=Ks[l];if(!a){var d,c,f;return o.size=(d=n.size)!==null&&d!==void 0?d:1,o.color=(c=n.color)!==null&&c!==void 0?c:"#ccc",o.label=(f=n.label)!==null&&f!==void 0?f:"",o}var h=Array.isArray(a)?a:[a];return Sr(s,h,n,t,e,r,Kn),typeof s.labelPosition=="number"&&(s.labelPosition=void 0),o}function Zs(a,n,t){var e,r;if(a==null)return t;if(typeof a=="function")return(e=a(n))!==null&&e!==void 0?e:t;if(Z(a)==="object"&&"when"in a){var i,o=a,s=o.when(n),l=s?o.then:o.else;return l===void 0?t:typeof l=="function"?(i=l(n))!==null&&i!==void 0?i:t:l??t}if(Z(a)==="object"&&"whenState"in a){var u,d=a,c=ln(d.whenState,n),f=c?d.then:d.else;return f===void 0?t:typeof f=="function"?(u=f(n))!==null&&u!==void 0?u:t:f??t}return(r=a)!==null&&r!==void 0?r:t}function ea(a,n){var t={};if(!a)return t;var e=Array.isArray(a)?a:[a],r=M(e),i;try{for(r.s();!(i=r.n()).done;){var o=i.value;if("when"in o&&"then"in o){var s=o.when(n),l=s?o.then:o.else;l&&Z(l)==="object"&&Xn(t,l,n)}else if("whenState"in o&&"then"in o){var u=ln(o.whenState,n),d=u?o.then:o.else;d&&Z(d)==="object"&&Xn(t,d,n)}else Xn(t,o,n)}}catch(c){r.e(c)}finally{r.f()}return t}function Xn(a,n,t){for(var e=0,r=Object.entries(n);e<r.length;e++){var i=Q(r[e],2),o=i[0],s=i[1];Zn.has(o)||(a[o]=Zs(s,t))}}var un=function(a){function n(){var t;return Y(this,n),t=te(this,n),t.rawEmitter=t,t}return ne(n,a),K(n)}(vr.EventEmitter);var Er=hr;function ta(a,n){var t=n.size;if(t!==0){var e=a.length;a.length+=t;var r=0;n.forEach(function(i){a[e+r]=i,r++})}}function Rr(a){a=a||{};for(var n=0,t=arguments.length<=1?0:arguments.length-1;n<t;n++){var e=n+1<1||arguments.length<=n+1?void 0:arguments[n+1];e&&Object.assign(a,e)}return a}function ot(a,n){for(var t in n)if(Object.prototype.hasOwnProperty.call(n,t)&&n[t]!==a[t])return!0;return!1}function Ar(a,n){var t=a,e=n;for(var r in t)if(Object.prototype.hasOwnProperty.call(t,r)&&t[r]!==e[r])return!1;for(var i in e)if(Object.prototype.hasOwnProperty.call(e,i)&&e[i]!==t[i])return!1;return!0}function We(a,n,t){t?a.add(n):a.delete(n)}var wr=Me(na());var Lr={easing:"quadraticInOut",duration:150};function Fe(a){return a.labelVisibility==="visible"&&a.visibility!=="hidden"}function aa(a){return a.backdropVisibility==="visible"&&a.visibility!=="hidden"}function dn(a){return[a.rotationAlignment==="graph"?1:0,a.labelRotationAlignment==="graph"?1:0]}function ra(a,n,t){var e=a[n];if(e)for(var r=0;r<e.length;r++){var i=e[r];if(!(t<i.offset||t>=i.offset+i.count)){if(i.count===1)e.splice(r,1);else if(t===i.offset)i.offset++,i.count--;else if(t===i.offset+i.count-1)i.count--;else{var o=t+1,s=i.offset+i.count-o;i.count=t-i.offset,e.splice(r+1,0,{offset:o,count:s})}return}}}function ia(a,n,t){if(!a[n]){a[n]=[{offset:t,count:1}];return}for(var e=a[n],r=e.length,i=0;i<e.length;i++)if(t<e[i].offset){r=i;break}var o=r>0?e[r-1]:null,s=r<e.length?e[r]:null,l=o&&o.offset+o.count===t,u=s&&t+1===s.offset;l&&u?(o.count+=1+s.count,e.splice(r,1)):l?o.count++:u?(s.offset--,s.count++):e.splice(r,0,{offset:t,count:1})}function Cr(a){if(!(0,wr.default)(a))throw new Error("Sigma: invalid graph instance.")}function cn(a){var n=Q(a.x,2),t=n[0],e=n[1],r=Q(a.y,2),i=r[0],o=r[1],s=Math.max(e-t,o-i),l=(e+t)/2,u=(o+i)/2;(s===0||Math.abs(s)===1/0||isNaN(s))&&(s=1),isNaN(l)&&(l=0),isNaN(u)&&(u=0);var d=function(f){return{x:.5+(f.x-l)/s,y:.5+(f.y-u)/s}};return d.applyTo=function(c){c.x=.5+(c.x-l)/s,c.y=.5+(c.y-u)/s},d.inverse=function(c){return{x:l+s*(c.x-.5),y:u+s*(c.y-.5)}},d.ratio=s,d}var hn={hideEdgesOnMove:!1,hideLabelsOnMove:!1,renderLabels:!0,renderEdgeLabels:!1,edgeLabelAnchors:"nodeLabels",enableEdgeEvents:!1,nodeLabelEvents:!1,edgeLabelEvents:!1,pickingDownSizingRatio:2,nodePickingPadding:0,edgePickingPadding:4,labelPickingPadding:10,stagePadding:30,minEdgeThickness:1.7,antiAliasingFeather:1,antialiasEdges:!0,antialiasNodes:!0,dragTimeout:100,draggedEventsTolerance:3,inertiaDuration:200,inertiaRatio:3,zoomDuration:250,zoomingRatio:1.7,doubleClickTimeout:300,doubleClickZoomingRatio:2.2,doubleClickZoomingDuration:200,tapMoveTolerance:10,zoomToSizeRatioFunction:Math.sqrt,itemSizesReference:"positions",autoRescale:!0,autoRescaleContent:"positions",enableNodeDrag:!1,getDraggedNodes:function(n){return[n]},dragPositionToAttributes:null,labelDensity:1,labelGridCellSize:100,labelRenderedSizeThreshold:6,labelPixelSnapping:!0,minCameraRatio:null,maxCameraRatio:null,enableCameraZooming:!0,enableCameraPanning:!0,enableCameraRotation:!0,enableCameraMouseRotation:!0,cameraPanBoundaries:null,gestureTarget:"graph",sharedGestureWheelMessage:"Use Ctrl + scroll to zoom the graph",sharedGestureAppleWheelMessage:"Use \u2318 + scroll to zoom the graph",sharedGestureTouchMessage:"Use two fingers to move the graph",allowInvalidContainer:!1,DEBUG_displayPickingLayer:!1,DEBUG_logShaders:!1,DEBUG_logRenderStats:!1,DEBUG_gpuTimerQueries:!1};function fn(a){if(typeof a.labelDensity!="number"||a.labelDensity<0)throw new Error("Settings: invalid `labelDensity`. Expecting a positive number.");var n=a.minCameraRatio,t=a.maxCameraRatio;if(typeof n=="number"&&typeof t=="number"&&t<n)throw new Error("Settings: invalid camera ratio boundaries. Expecting `maxCameraRatio` to be greater than `minCameraRatio`.")}function Pr(a){return Rr({},hn,a)}var Qs=new Set(["italic","oblique"]),Js=new Set(["bold","bolder","lighter"]);function gn(a){for(var n="normal",t="normal",e=a.trim(),r=e.split(/\s+/),i=0,o=0;o<r.length;o++){var s=r[o].toLowerCase();if(Qs.has(s))t=s,i=o+1;else if(Js.has(s)||/^\d{3}$/.test(s))n=s,i=o+1;else if(s==="normal")i=o+1;else break}var l=r.slice(i).join(" ");return{family:l||e,weight:n,style:t}}function st(a,n,t){var e=document.createElement(a);if(n)for(var r in n)e.style[r]=n[r];if(t)for(var i in t)e.setAttribute(i,t[i]);return e}function Dt(){return typeof window.devicePixelRatio<"u"?window.devicePixelRatio:1}var Or=Me(Ke());function el(a){var n=a.type===WebGL2RenderingContext.FLOAT&&!a.normalized,t=a.type===WebGL2RenderingContext.UNSIGNED_BYTE&&a.size===4&&a.normalized;if(!n&&!t)throw new Error('Attribute "'.concat(a.name,'" is invalid: only non-normalized FLOAT and normalized UNSIGNED_BYTE with size 4 are supported.'));return a.normalized?1:a.size}function oa(a){var n=0;return a.forEach(function(t){return n+=el(t)}),n}function Ur(a,n,t){var e=a==="VERTEX"?n.VERTEX_SHADER:n.FRAGMENT_SHADER,r=n.createShader(e);if(r===null)throw new Error("loadShader: error while creating the shader");n.shaderSource(r,t),n.compileShader(r);var i=n.getShaderParameter(r,n.COMPILE_STATUS);if(!i){var o=n.getShaderInfoLog(r);throw n.deleteShader(r),new Error(`loadShader: error while compiling the shader:
`.concat(o,`
`).concat(t))}return r}function la(a,n){return Ur("VERTEX",a,n)}function ua(a,n){return Ur("FRAGMENT",a,n)}function da(a,n){var t=a.createProgram();if(t===null)throw new Error("loadProgram: error while creating the program.");var e,r;for(e=0,r=n.length;e<r;e++)a.attachShader(t,n[e]);a.linkProgram(t);var i=a.getProgramParameter(t,a.LINK_STATUS);if(!i){var o=a.getProgramInfoLog(t);throw a.deleteProgram(t),new Error("loadProgram: error while linking the program: ".concat(o))}return t}function kr(a){var n=a.gl,t=a.buffer,e=a.program,r=a.vertexShader,i=a.fragmentShader;n.deleteShader(r),n.deleteShader(i),n.deleteProgram(e),n.deleteBuffer(t)}function ae(a){return a%1===0?a.toFixed(1):a.toString()}var xn=new Map,Hr=new Map,tl=0;function $r(a,n){var t,e=(t=a.variables)===null||t===void 0||(t=t[n.source||n.name.replace(/^a_/,"")])===null||t===void 0?void 0:t.default,r=typeof e=="number"?e:typeof n.defaultValue=="number"?n.defaultValue:0;return ae(r)}function _n(a,n,t){var e,r=arguments.length>3&&arguments[3]!==void 0?arguments[3]:function(o){return"v_".concat(o.name.replace(/^a_/,""))},i=[n,t].concat($(a.uniforms.filter(function(o){return o.type==="float"}).map(function(o){var s;return ae((s=o.value)!==null&&s!==void 0?s:0)})),$(((e=a.attributes)!==null&&e!==void 0?e:[]).map(r)));return"sdf_".concat(a.name,"(").concat(i.join(", "),")")}function nl(a){var n,t=a.name,e=a.uniforms.filter(function(o){return o.type==="float"&&o.value!==void 0&&o.value!==0}).map(function(o){return"".concat(o.name.replace("u_",""),"=").concat(o.value)}).sort(),r=((n=a.attributes)!==null&&n!==void 0?n:[]).map(function(o){var s;return"".concat(o.name,"@").concat((s=o.source)!==null&&s!==void 0?s:"","=").concat($r(a,o))}),i=[].concat($(e),$(r));return i.length>0&&(t+="#"+i.join("#")),t}function al(a){var n=nl(a);if(!xn.has(n)){var t={},e=M(a.uniforms),r;try{for(e.s();!(r=e.n()).done;){var i=r.value;i.type==="float"&&i.value!==void 0&&(t[i.name]=i.value)}}catch(o){e.e(o)}finally{e.f()}xn.set(n,{shape:a,uniformValues:t,slug:n}),Hr.set(n,tl++)}return n}function kt(a){var n;return(n=Hr.get(a))!==null&&n!==void 0?n:-1}function Vr(a){var n=[],t=new Set,e=new Set,r=/mat2 rotate2D\(float angle\)\s*\{[^}]+\}/,i=M(a),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;if(!e.has(s.name)){e.add(s.name);var l=s.glsl;r.test(l)&&(t.has("rotate2D")?l=l.replace(r,""):t.add("rotate2D")),n.push(l)}}}catch(u){i.e(u)}finally{i.f()}return n.join(`
`)}function rl(){return Vr(Array.from(xn.values()).map(function(a){return a.shape}))}function il(a){var n=Array.from(xn.entries());if(n.length===0)return`
float querySDF(int shapeId, vec2 uv, float size) {
  return length(uv) - size;
}
`;var t=n.map(function(e,r){var i=Q(e,2),o=i[0],s=i[1].shape,l=_n(s,"uv","size",function(u){var d=u.name.replace(/^a_/,"");return a!=null&&a.has(d)?"g_".concat(d):$r(s,u)});return"    case ".concat(r,": return ").concat(l,"; // ").concat(o)}).join(`
`);return`
float querySDF(int shapeId, vec2 uv, float size) {
  switch (shapeId) {
`.concat(t,`
    default: return length(uv) - size;
  }
}
`)}function ca(a){return Vr(a)}function Ft(a){return $(new Map(a.flatMap(function(n){return n.uniforms}).map(function(n){return[n.name,n]})).values())}function ol(a,n){if(a.length===0)return`
void queryNodeSDF(int shapeId, vec2 uv, float size) {
  context.sdf = length(uv) - size;
  context.inradiusFactor = 1.0;
}
`;var t=function(c){return _n(c,"uv","size")},e=function(c){var f,h;return(f=c.inradiusFactorGLSL)!==null&&f!==void 0?f:ae((h=c.inradiusFactor)!==null&&h!==void 0?h:1)};if(a.length===1){var r=a[0];return`
void queryNodeSDF(int shapeId, vec2 uv, float size) {
  context.sdf = `.concat(t(r),`;
  context.inradiusFactor = `).concat(e(r),`;
}
`)}var i=a.map(function(d,c){return"    case ".concat(c,": // ").concat(d.name,`
      context.sdf = `).concat(t(d),`;
      context.inradiusFactor = `).concat(e(d),`;
      break;`)}).join(`
`),o=a[0],s="",l="shapeId";if(n&&n.length>1){var u=n.map(function(d,c){return"    case ".concat(d,": return ").concat(c,"; // ").concat(a[c].name)}).join(`
`);s=`
int globalToLocalShapeId(int globalId) {
  switch (globalId) {
`.concat(u,`
    default: return 0;
  }
}
`),l="globalToLocalShapeId(shapeId)"}return"".concat(s,`
void queryNodeSDF(int shapeId, vec2 uv, float size) {
  switch (`).concat(l,`) {
`).concat(i,`
    default:
      context.sdf = `).concat(t(o),`;
      context.inradiusFactor = `).concat(e(o),`;
  }
}
`)}var ut={right:0,left:1,above:2,below:3,over:4},dt=5,ha=3,Xr=`
float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
float nodeRadiusGraphSpace = nodeSize * u_correctionRatio / u_sizeRatio * 2.0;
float nodeRadiusNDC = nodeRadiusGraphSpace * matrixScaleX;
float nodeRadiusPixels = nodeRadiusNDC * u_resolution.x / 2.0;
`,sl=`
mat2 rotate2D(float angle) {
  float c = cos(angle);
  float s = sin(angle);
  return mat2(c, -s, s, c);
}
`,jr=`
vec2 getLabelDirection(float positionMode) {
  if (positionMode < 0.5) return vec2(1.0, 0.0);   // Right
  if (positionMode < 1.5) return vec2(-1.0, 0.0);  // Left
  if (positionMode < 2.5) return vec2(0.0, -1.0);  // Above
  if (positionMode < 3.5) return vec2(0.0, 1.0);   // Below
  return vec2(0.0);                                 // Over (centered)
}
`,ll=`
float sdfBox(vec2 p, vec2 halfSize) {
  vec2 d = abs(p) - halfSize;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}
`,ul=`
float sdfRotatedBox(vec2 p, vec2 halfSize, float angle) {
  float c = cos(-angle);
  float s = sin(-angle);
  vec2 rotatedP = mat2(c, -s, s, c) * p;
  return sdfBox(rotatedP, halfSize);
}
`,dl=`
float sdfRoundedBox(vec2 p, vec2 halfSize, float radius) {
  vec2 d = abs(p) - halfSize + radius;
  return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - radius;
}
`,cl=`
float sdfRoundedRotatedBox(vec2 p, vec2 halfSize, float angle, float radius) {
  float c = cos(-angle);
  float s = sin(-angle);
  vec2 rotatedP = mat2(c, -s, s, c) * p;
  return sdfRoundedBox(rotatedP, halfSize, radius);
}
`,qr=`
vec2 labelBoxCenter(float positionMode, float labelStart, vec2 halfSize, float textHalfY) {
  if (positionMode < 0.5) return vec2(labelStart + halfSize.x, 0.0);    // right
  if (positionMode < 1.5) return vec2(-(labelStart + halfSize.x), 0.0); // left
  if (positionMode < 2.5) return vec2(0.0, -(labelStart + textHalfY));  // above
  if (positionMode < 3.5) return vec2(0.0, labelStart + textHalfY);     // below
  return vec2(0.0);                                                     // over
}
`,fa=2,Le=`
vec4 readNodeData(sampler2D nodeDataTexture, int nodeDataTextureWidth, int nodeIndex) {
  int t = nodeIndex * `.concat(fa,`;
  ivec2 coord = ivec2(t % nodeDataTextureWidth, t / nodeDataTextureWidth);
  return texelFetch(nodeDataTexture, coord, 0);
}
`),Ue=`
vec4 readNodeFlags(sampler2D nodeDataTexture, int nodeDataTextureWidth, int nodeIndex) {
  int t = nodeIndex * `.concat(fa,` + 1;
  ivec2 coord = ivec2(t % nodeDataTextureWidth, t / nodeDataTextureWidth);
  return texelFetch(nodeDataTexture, coord, 0);
}
`),hl=`
vec4 readNodeColor(sampler2D nodeDataTexture, int nodeDataTextureWidth, int nodeIndex) {
  int t = nodeIndex * `.concat(fa,` + 1;
  ivec2 coord = ivec2(t % nodeDataTextureWidth, t / nodeDataTextureWidth);
  vec4 texel = texelFetch(nodeDataTexture, coord, 0);
  float r = floor(texel.b / 65536.0);
  float g = floor(mod(texel.b, 65536.0) / 256.0);
  float b = mod(texel.b, 256.0);
  return vec4(r / 255.0, g / 255.0, b / 255.0, texel.a);
}
`),ct=`
vec4 readFrameTexel(sampler2D frameTexture, int frameTextureWidth, int index) {
  ivec2 coord = ivec2(index % frameTextureWidth, index / frameTextureWidth);
  return texelFetch(frameTexture, coord, 0);
}
`;function fl(a,n){var t=function(o){return _n(o,"uv","size")};if(a.length===1)return{code:Fr(t(a[0])),multiShape:!1};var e=a.map(function(i,o){return"    case ".concat(n?n[o]:o,": return ").concat(t(i),";")}).join(`
`),r=`
float queryShapeSDF(int shapeId, vec2 uv, float size) {
  switch (shapeId) {
`.concat(e,`
    default: return `).concat(t(a[0]),`;
  }
}
int g_shapeId;
`).concat(Fr("queryShapeSDF(g_shapeId, uv, size)"),`
`);return{code:r,multiShape:!0}}function Fr(a){return`
float findEdgeDistance(vec2 direction, float size) {
  float lo = 0.0, hi = 2.0;
  for (int i = 0; i < 8; i++) {
    float mid = (lo + hi) * 0.5;
    vec2 uv = direction * mid;
    if (`.concat(a,` < 0.0) lo = mid; else hi = mid;
  }
  return (lo + hi) * 0.5;
}
`)}function gl(a,n){for(;!{}.hasOwnProperty.call(a,n)&&(a=Be(a))!==null;);return a}function sa(){return sa=typeof Reflect<"u"&&Reflect.get?Reflect.get.bind():function(a,n,t){var e=gl(a,n);if(e){var r=Object.getOwnPropertyDescriptor(e,n);return r.get?r.get.call(arguments.length<3?a:t):r.value}},sa.apply(null,arguments)}function ie(a,n,t,e){var r=sa(Be(1&e?a.prototype:a),n,t);return 2&e&&typeof r=="function"?function(i){return r.apply(t,i)}:r}var vl=1024,pl=1.5,Yr=-1,Tn=function(){function a(n,t){var e=arguments.length>2&&arguments[2]!==void 0?arguments[2]:vl;Y(this,a),S(this,"texture",null),S(this,"dirty",!1),S(this,"dirtyRangeStart",1/0),S(this,"dirtyRangeEnd",-1),S(this,"indexMap",new Map),S(this,"freeIndices",[]),S(this,"nextIndex",0),this.gl=n,this.maxTextureSize=n.getParameter(n.MAX_TEXTURE_SIZE),this.TEXELS_PER_ITEM=t,this.capacity=this.roundUpToPowerOfTwo(e);var r=this.computeTextureDimensions(this.capacity);this.textureWidth=r.width,this.textureHeight=r.height,this.data=new Float32Array(this.textureWidth*this.textureHeight*4),this.createTexture()}return K(a,[{key:"computeTextureDimensions",value:function(t){var e=t*this.TEXELS_PER_ITEM,r=Math.min(e,this.maxTextureSize),i=Math.ceil(e/r);return{width:r,height:i}}},{key:"roundUpToPowerOfTwo",value:function(t){return Math.pow(2,Math.ceil(Math.log2(Math.max(1,t))))}},{key:"createTexture",value:function(){var t=this.gl;this.texture=t.createTexture(),t.activeTexture(t.TEXTURE0),t.bindTexture(t.TEXTURE_2D,this.texture),t.texImage2D(t.TEXTURE_2D,0,t.RGBA32F,this.textureWidth,this.textureHeight,0,t.RGBA,t.FLOAT,this.data),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MIN_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MAG_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_S,t.CLAMP_TO_EDGE),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_T,t.CLAMP_TO_EDGE),t.bindTexture(t.TEXTURE_2D,null)}},{key:"resize",value:function(t){if(!(t<=this.capacity)){var e=this.roundUpToPowerOfTwo(Math.ceil(t*pl)),r=this.gl,i=this.computeTextureDimensions(e),o=new Float32Array(i.width*i.height*4);o.set(this.data),this.texture&&r.deleteTexture(this.texture),this.data=o,this.capacity=e,this.textureWidth=i.width,this.textureHeight=i.height,this.createTexture(),this.dirty=!0,this.dirtyRangeStart=0,this.dirtyRangeEnd=this.nextIndex}}},{key:"allocate",value:function(t){var e=this.indexMap.get(t);if(e!==void 0)return e;var r;return this.freeIndices.length>0?r=this.freeIndices.pop():(r=this.nextIndex++,r>=this.capacity&&this.resize(r+1)),this.indexMap.set(t,r),r}},{key:"free",value:function(t){var e=this.indexMap.get(t);if(e!==void 0){this.indexMap.delete(t),this.freeIndices.push(e);for(var r=e*this.TEXELS_PER_ITEM*4,i=0;i<this.TEXELS_PER_ITEM*4;i++)this.data[r+i]=0;this.markDirty(e)}}},{key:"getIndex",value:function(t){var e;return(e=this.indexMap.get(t))!==null&&e!==void 0?e:-1}},{key:"has",value:function(t){return this.indexMap.has(t)}},{key:"markDirty",value:function(t){this.dirty=!0,this.dirtyRangeStart=Math.min(this.dirtyRangeStart,t),this.dirtyRangeEnd=Math.max(this.dirtyRangeEnd,t+1)}},{key:"upload",value:function(){if(!(!this.dirty||!this.texture)){var t=this.gl,e=this.textureWidth;t.activeTexture(t.TEXTURE0),t.bindTexture(t.TEXTURE_2D,this.texture);var r=this.dirtyRangeStart*this.TEXELS_PER_ITEM,i=Math.min(this.dirtyRangeEnd*this.TEXELS_PER_ITEM,this.capacity*this.TEXELS_PER_ITEM);if(r<i)for(var o=Math.floor(r/e),s=Math.floor((i-1)/e),l=o;l<=s;l++){var u=l*e,d=Math.min(u+e,this.capacity*this.TEXELS_PER_ITEM),c=Math.max(r,u),f=Math.min(i,d);if(c<f){var h=c-u,g=f-c,m=this.data.subarray(c*4,f*4);t.texSubImage2D(t.TEXTURE_2D,0,h,l,g,1,t.RGBA,t.FLOAT,m)}}t.bindTexture(t.TEXTURE_2D,null),this.dirty=!1,this.dirtyRangeStart=1/0,this.dirtyRangeEnd=-1}}},{key:"bind",value:function(t){var e=this.gl;e.activeTexture(e.TEXTURE0+t),e.bindTexture(e.TEXTURE_2D,this.texture)}},{key:"getTexture",value:function(){return this.texture}},{key:"getCapacity",value:function(){return this.capacity}},{key:"getTextureWidth",value:function(){return this.textureWidth}},{key:"getTextureHeight",value:function(){return this.textureHeight}},{key:"getTexelsPerItem",value:function(){return this.TEXELS_PER_ITEM}},{key:"getCount",value:function(){return this.indexMap.size}},{key:"getHighWaterMark",value:function(){return this.nextIndex}},{key:"isDirty",value:function(){return this.dirty}},{key:"clear",value:function(){this.indexMap.clear(),this.freeIndices=[],this.nextIndex=0,this.data.fill(0),this.dirty=!0,this.dirtyRangeStart=0,this.dirtyRangeEnd=this.capacity}},{key:"restore",value:function(){this.createTexture(),this.dirty=!1,this.dirtyRangeStart=1/0,this.dirtyRangeEnd=-1}},{key:"kill",value:function(){this.texture&&(this.gl.deleteTexture(this.texture),this.texture=null),this.indexMap.clear(),this.freeIndices=[]}}])}();function me(a){var n={},t={},e=0,r=M(a),i;try{for(r.s();!(i=r.n()).done;){var o=i.value,s=M(o.attributes),l;try{for(s.s();!(l=s.n()).done;){var u=l.value,d=u.name.replace(/^a_/,"");d in n||(n[d]=e,t[d]=u,e+=u.size)}}catch(c){s.e(c)}finally{s.f()}}}catch(c){r.e(c)}finally{r.f()}return{floatsPerItem:e,texelsPerItem:Math.max(1,Math.ceil(e/4)),offsets:n,specs:t}}var Sn=function(a){function n(t,e,r){var i;return Y(this,n),i=te(this,n,[t,e.texelsPerItem,r]),i.floatsPerItem=e.floatsPerItem,i}return ne(n,a),K(n,[{key:"updateAllAttributes",value:function(e,r){var i=this.indexMap.get(e);i===void 0&&(i=this.allocate(e));for(var o=i*this.TEXELS_PER_ITEM*4,s=Math.min(r.length,this.floatsPerItem),l=0;l<s;l++)this.data[o+l]=r[l];this.markDirty(i)}},{key:"updateAllAttributesAtRow",value:function(e,r){e>=this.capacity&&this.resize(e+1);for(var i=e*this.TEXELS_PER_ITEM*4,o=Math.min(r.length,this.floatsPerItem),s=0;s<o;s++)this.data[i+s]=r[s];this.markDirty(e)}}])}(Tn);function En(a,n,t){for(var e=[],r=new Set,i=0;i<a.length;i++){var o=a[i],s=M(o.attributes),l;try{for(s.s();!(l=s.n()).done;){var u=l.value,d=u.name.replace(/^a_/,"");if(!r.has(d)){r.add(d);var c=n.offsets[d];if(c!==void 0){var f=t?.get(i);e.push({sourceKey:u.source||d,packedOffset:c,size:u.size,isColor:u.size===4&&!!u.normalized,defaultNum:typeof u.defaultValue=="number"?u.defaultValue:u.defaultValue===!0?1:0,defaultColor:typeof u.defaultValue=="string"?u.defaultValue:"",sourceIndex:i,hasLifecycleHook:!!(f!=null&&f.getAttributeData)})}}}}catch(h){s.e(h)}finally{s.f()}}return e}function Rn(a,n,t,e,r,i){t.fill(0);for(var o=0,s=a.length;o<s;o++){var l=a[o],u=l.packedOffset,d=void 0;if(l.hasLifecycleHook){var c=r.get(l.sourceIndex-i);d=c.getAttributeData(n,l.sourceKey),d===null&&(d=n[l.sourceKey])}else d=n[l.sourceKey];if(l.isColor){var f=typeof d=="string"?d:l.defaultColor||e,h=ke(f),g=Q(h,4),m=g[0],p=g[1],v=g[2],b=g[3];t[u]=m/255,t[u+1]=p/255,t[u+2]=v/255,t[u+3]=b/255}else if(l.size===1)t[u]=typeof d=="number"?d:typeof d=="boolean"?d?1:0:l.defaultNum;else{var y=Array.isArray(d)?d:null;if(y)for(var T=0;T<l.size;T++){var x;t[u+T]=(x=y[T])!==null&&x!==void 0?x:0}}}}var vn=["r","g","b","a"];function lt(a,n){var t=a.offsets,e=a.specs,r=a.texelsPerItem,i=a.floatsPerItem,o=Object.keys(t);if(o.length===0||i===0)return{fetchCode:"",varyingAssignments:""};var s=n.varPrefix,l=n.baseTexelExpr,u=n.textureWidthUniform,d=n.textureSamplerUniform,c=n.outputPrefix,f=c===void 0?"v_":c,h=[];h.push("  int ".concat(s,"BaseTexel = ").concat(l,";")),h.push("");for(var g=0;g<r;g++)h.push("  ivec2 ".concat(s,"Coord").concat(g," = ivec2((").concat(s,"BaseTexel + ").concat(g,") % ").concat(u,", (").concat(s,"BaseTexel + ").concat(g,") / ").concat(u,");")),h.push("  vec4 ".concat(s,"Texel").concat(g," = texelFetch(").concat(d,", ").concat(s,"Coord").concat(g,", 0);"));h.push("");for(var m=[],p=function(){var T=b[v],x=e[T],_=t[T],R=Math.floor(_/4),E=_%4,L="".concat(s,"Texel").concat(R),D="".concat(s,"Texel").concat(R+1),F="".concat(s,"Fetched_").concat(T);if(x.size===1)h.push("  float ".concat(F," = ").concat(L,".").concat(vn[E],";"));else if(x.size===4&&E===0)h.push("  vec4 ".concat(F," = ").concat(L,";"));else{var A=E+x.size;if(A<=4){var I="vec".concat(x.size),w=vn.slice(E,A).join("");h.push("  ".concat(I," ").concat(F," = ").concat(L,".").concat(w,";"))}else{var k=x.size===4?"vec4":"vec".concat(x.size),G=vn.slice(E).map(function(C){return"".concat(L,".").concat(C)}),N=vn.slice(0,A-4).map(function(C){return"".concat(D,".").concat(C)}),P=[].concat($(G),$(N)).join(", ");h.push("  ".concat(k," ").concat(F," = ").concat(k,"(").concat(P,");"))}}m.push("  ".concat(f).concat(T," = ").concat(F,";"))},v=0,b=o;v<b.length;v++)p();return{fetchCode:h.join(`
`),varyingAssignments:m.join(`
`)}}function ga(a,n,t){if(!(!n||t.type==="sampler2D"))switch(t.type){case"float":a.uniform1f(n,t.value);break;case"int":case"bool":a.uniform1i(n,t.value);break;case"vec2":a.uniform2fv(n,t.value);break;case"vec3":a.uniform3fv(n,t.value);break;case"vec4":a.uniform4fv(n,t.value);break;case"mat3":a.uniformMatrix3fv(n,!1,t.value);break;case"mat4":a.uniformMatrix4fv(n,!1,t.value);break}}var ml=S(S(S(S(S(S(S(S({},WebGL2RenderingContext.BOOL,1),WebGL2RenderingContext.BYTE,1),WebGL2RenderingContext.UNSIGNED_BYTE,1),WebGL2RenderingContext.SHORT,2),WebGL2RenderingContext.UNSIGNED_SHORT,2),WebGL2RenderingContext.INT,4),WebGL2RenderingContext.UNSIGNED_INT,4),WebGL2RenderingContext.FLOAT,4);function pn(a){var n=a.match(/^(#version[^\n]*\n)/);return n?n[1]+`#define PICKING_MODE
`+a.slice(n[1].length):`#define PICKING_MODE
`+a}var He=function(){function a(n,t,e){Y(this,a),S(this,"floats",new Float32Array),S(this,"ints",new Uint32Array),S(this,"constantArray",new Float32Array),S(this,"capacity",0),S(this,"verticesCount",0),S(this,"bufferGeneration",0),S(this,"uploadedGeneration",new Map),S(this,"constantBufferGeneration",0),S(this,"uploadedConstantGeneration",new Map),S(this,"renderOffset",0),S(this,"renderCount",-1),S(this,"debugStats",{drawCalls:0,verticesDrawn:0,bufferUploadBytes:0}),S(this,"shadersLogged",!1),S(this,"pickProgram",null);var r=this.getDefinition();if(this.VERTICES=r.VERTICES,this.VERTEX_SHADER_SOURCE=r.VERTEX_SHADER_SOURCE,this.FRAGMENT_SHADER_SOURCE=r.FRAGMENT_SHADER_SOURCE,this.UNIFORMS=r.UNIFORMS,this.ATTRIBUTES=r.ATTRIBUTES,this.METHOD=r.METHOD,this.CONSTANT_ATTRIBUTES="CONSTANT_ATTRIBUTES"in r?r.CONSTANT_ATTRIBUTES:[],this.CONSTANT_DATA="CONSTANT_DATA"in r?r.CONSTANT_DATA:[],this.isInstanced="CONSTANT_ATTRIBUTES"in r,this.ATTRIBUTES_ITEMS_COUNT=oa(this.ATTRIBUTES),this.STRIDE=this.VERTICES*this.ATTRIBUTES_ITEMS_COUNT,this.renderer=e,this.normalProgram=this.getProgramInfo("normal",n,r.VERTEX_SHADER_SOURCE,r.FRAGMENT_SHADER_SOURCE,null),this.pickProgram=this.getProgramInfo("pick",n,pn(r.VERTEX_SHADER_SOURCE),pn(r.FRAGMENT_SHADER_SOURCE),null),this.isInstanced){var i=oa(this.CONSTANT_ATTRIBUTES);if(this.CONSTANT_DATA.length!==this.VERTICES)throw new Error("Program: error while getting constant data (expected ".concat(this.VERTICES," items, received ").concat(this.CONSTANT_DATA.length," instead)"));this.constantArray=new Float32Array(this.CONSTANT_DATA.length*i);for(var o=0;o<this.CONSTANT_DATA.length;o++){var s=this.CONSTANT_DATA[o];if(s.length!==i)throw new Error("Program: error while getting constant data (one vector has ".concat(s.length," items instead of ").concat(i,")"));for(var l=0;l<s.length;l++)this.constantArray[o*i+l]=s[l]}this.STRIDE=this.ATTRIBUTES_ITEMS_COUNT}}return K(a,[{key:"kill",value:function(){kr(this.normalProgram),this.pickProgram&&kr(this.pickProgram)}},{key:"resetDebugStats",value:function(){this.debugStats.drawCalls=0,this.debugStats.verticesDrawn=0,this.debugStats.bufferUploadBytes=0}},{key:"getProgramInfo",value:function(t,e,r,i,o){var s=e.createBuffer();if(s===null)throw new Error("Program: error while creating the WebGL buffer.");var l=la(e,r),u=ua(e,i),d=da(e,[l,u]),c={};this.UNIFORMS.forEach(function(g){var m=e.getUniformLocation(d,g);m&&(c[g]=m)});var f={};this.ATTRIBUTES.forEach(function(g){f[g.name]=e.getAttribLocation(d,g.name)});var h;if(this.isInstanced&&(this.CONSTANT_ATTRIBUTES.forEach(function(g){f[g.name]=e.getAttribLocation(d,g.name)}),h=e.createBuffer(),h===null))throw new Error("Program: error while creating the WebGL constant buffer.");return{name:t,program:d,gl:e,frameBuffer:o,buffer:s,constantBuffer:h||{},uniformLocations:c,attributeLocations:f,isPicking:t==="pick",vertexShader:l,fragmentShader:u}}},{key:"bindProgram",value:function(t){var e=this,r=0,i=t.gl,o=t.buffer;if(this.isInstanced){if(i.bindBuffer(i.ARRAY_BUFFER,t.constantBuffer),r=0,this.CONSTANT_ATTRIBUTES.forEach(function(d){return r+=e.bindAttribute(d,t,r,!1)}),this.uploadedConstantGeneration.get(t.constantBuffer)!==this.constantBufferGeneration){var l;i.bufferData(i.ARRAY_BUFFER,this.constantArray,i.STATIC_DRAW),this.uploadedConstantGeneration.set(t.constantBuffer,this.constantBufferGeneration),(l=this.renderer)!==null&&l!==void 0&&l.getSetting("DEBUG_logRenderStats")&&(this.debugStats.bufferUploadBytes+=this.constantArray.byteLength)}if(i.bindBuffer(i.ARRAY_BUFFER,t.buffer),r=this.renderOffset*this.ATTRIBUTES_ITEMS_COUNT*Float32Array.BYTES_PER_ELEMENT,this.ATTRIBUTES.forEach(function(d){return r+=e.bindAttribute(d,t,r,!0)}),this.uploadedGeneration.get(o)!==this.bufferGeneration){var u;i.bufferData(i.ARRAY_BUFFER,this.floats,i.DYNAMIC_DRAW),this.uploadedGeneration.set(o,this.bufferGeneration),(u=this.renderer)!==null&&u!==void 0&&u.getSetting("DEBUG_logRenderStats")&&(this.debugStats.bufferUploadBytes+=this.floats.byteLength)}}else if(i.bindBuffer(i.ARRAY_BUFFER,o),r=0,this.ATTRIBUTES.forEach(function(d){return r+=e.bindAttribute(d,t,r)}),this.uploadedGeneration.get(o)!==this.bufferGeneration){var s;i.bufferData(i.ARRAY_BUFFER,this.floats,i.DYNAMIC_DRAW),this.uploadedGeneration.set(o,this.bufferGeneration),(s=this.renderer)!==null&&s!==void 0&&s.getSetting("DEBUG_logRenderStats")&&(this.debugStats.bufferUploadBytes+=this.floats.byteLength)}i.bindBuffer(i.ARRAY_BUFFER,null)}},{key:"unbindProgram",value:function(t){var e=this;this.isInstanced?(this.CONSTANT_ATTRIBUTES.forEach(function(r){return e.unbindAttribute(r,t,!1)}),this.ATTRIBUTES.forEach(function(r){return e.unbindAttribute(r,t,!0)})):this.ATTRIBUTES.forEach(function(r){return e.unbindAttribute(r,t)})}},{key:"bindAttribute",value:function(t,e,r,i){var o=ml[t.type];if(typeof o!="number")throw new Error('Program.bind: yet unsupported attribute type "'.concat(t.type,'"'));var s=e.attributeLocations[t.name],l=e.gl;if(s!==-1){l.enableVertexAttribArray(s);var u=this.isInstanced?(i?this.ATTRIBUTES_ITEMS_COUNT:oa(this.CONSTANT_ATTRIBUTES))*Float32Array.BYTES_PER_ELEMENT:this.ATTRIBUTES_ITEMS_COUNT*Float32Array.BYTES_PER_ELEMENT;l.vertexAttribPointer(s,t.size,t.type,t.normalized||!1,u,r),this.isInstanced&&i&&l.vertexAttribDivisor(s,1)}return t.size*o}},{key:"unbindAttribute",value:function(t,e,r){var i=e.attributeLocations[t.name],o=e.gl;i!==-1&&(o.disableVertexAttribArray(i),this.isInstanced&&r&&o.vertexAttribDivisor(i,0))}},{key:"reallocate",value:function(t){t!==this.capacity&&(this.capacity=t,this.verticesCount=this.VERTICES*t,this.floats=new Float32Array(this.isInstanced?this.capacity*this.ATTRIBUTES_ITEMS_COUNT:this.verticesCount*this.ATTRIBUTES_ITEMS_COUNT),this.ints=new Uint32Array(this.floats.buffer),this.invalidateBuffers())}},{key:"invalidateBuffers",value:function(){this.bufferGeneration++,this.constantBufferGeneration++}},{key:"hasNothingToRender",value:function(){return this.verticesCount===0}},{key:"setTypedUniform",value:function(t,e){var r;ga(e.gl,(r=e.uniformLocations[t.name])!==null&&r!==void 0?r:null,t)}},{key:"renderProgram",value:function(t,e){var r=e.gl,i=e.program,o=e.isPicking;o?r.disable(r.BLEND):r.enable(r.BLEND),r.useProgram(i),this.setUniforms(t,e),this.drawWebGL(this.METHOD,e)}},{key:"render",value:function(t,e,r){var i;if(!this.shadersLogged&&(i=this.renderer)!==null&&i!==void 0&&i.getSetting("DEBUG_logShaders")&&(this.shadersLogged=!0,console.log("[sigma] DEBUG_logShaders: ".concat(this.constructor.name),{normal:{vertexShaderSource:this.VERTEX_SHADER_SOURCE,fragmentShaderSource:this.FRAGMENT_SHADER_SOURCE},pick:{vertexShaderSource:pn(this.VERTEX_SHADER_SOURCE),fragmentShaderSource:pn(this.FRAGMENT_SHADER_SOURCE)}})),!this.hasNothingToRender()){this.renderOffset=e??0,this.renderCount=r??-1;var o=this.normalProgram.gl;if(o.bindFramebuffer(o.FRAMEBUFFER,null),o.viewport(0,0,t.width*t.pixelRatio,t.height*t.pixelRatio),this.bindProgram(this.normalProgram),this.renderProgram(t,this.normalProgram),this.unbindProgram(this.normalProgram),this.pickProgram&&t.pickingFrameBuffer){var s=Math.ceil(t.width*t.pixelRatio/t.downSizingRatio),l=Math.ceil(t.height*t.pixelRatio/t.downSizingRatio);o.bindFramebuffer(o.FRAMEBUFFER,t.pickingFrameBuffer),o.viewport(0,0,s,l),this.bindProgram(this.pickProgram),this.renderProgram(t,this.pickProgram),this.unbindProgram(this.pickProgram),o.bindFramebuffer(o.FRAMEBUFFER,null),o.viewport(0,0,t.width*t.pixelRatio,t.height*t.pixelRatio)}}}},{key:"drawWebGL",value:function(t,e){var r,i=e.gl,o=this.renderCount>=0?this.renderCount:this.capacity;(r=this.renderer)!==null&&r!==void 0&&r.getSetting("DEBUG_logRenderStats")&&(this.debugStats.drawCalls++,this.debugStats.verticesDrawn+=o*this.VERTICES),this.isInstanced?i.drawArraysInstanced(t,0,this.VERTICES,o):i.drawArrays(t,this.renderOffset*this.VERTICES,o*this.VERTICES)}}])}(),Ge=2,It=7,Kr={below:0,above:1,left:2,right:3};function bl(){var a=`#version 300 es
precision highp float;

uniform mat3 u_matrix;
uniform vec2 u_resolution;
uniform float u_labelPixelSnapping;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform float u_pixelRatio;
uniform float u_labelMargin;
uniform float u_zoomLabelSizeRatio;

uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;

// Atlas size is fixed at 2048\xD72048 \u2014 matches AttachmentManager.ATLAS_SIZE.
uniform sampler2D u_atlasTexture;
const vec2 u_atlasSize = vec2(2048.0);

// Per-instance
in float a_nodeIndex;           // node-data texture index
in vec4 a_atlasRect;            // x, y, width, height in atlas pixels
in vec2 a_attachmentSize;       // attachment dimensions (CSS px)
in float a_positionMode;        // label position: 0=right 1=left 2=above 3=below 4=over
in float a_attachmentPlacement; // 0=below 1=above 2=left 3=right (relative to label)
in float a_labelWidth;          // label width (CSS px)
in float a_labelHeight;         // label height: font line box (CSS px)
in float a_textHeight;          // actual glyph height (CSS px)
in float a_labelAngle;          // label rotation angle (radians)

// Per-vertex (constant)
in vec2 a_quadCorner;           // [-1,-1], [1,-1], [-1,1], [1,1]

out vec2 v_texCoord;

`.concat(Le,`
`).concat(Ue,`
`).concat(ct,`
`).concat(qr,`
`).concat(sl,`

void main() {
  int nodeIdx = int(a_nodeIndex);

  // Node data: (x, y, size, shapeId).
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 nodePos = nodeData.xy;
  float nodeSize = nodeData.z;

  // Normalized edge distance from the shared frame texture (the frame-pass ran
  // the SDF search once; we just read the result).
  float edgeDist = readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;

  // Per-node label rotation alignment: 0 = viewport, 1 = label turns with camera.
  float labelRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).g;

  vec3 nodeClip = u_matrix * vec3(nodePos, 1.0);

  // Node radius in physical pixels (matches label/background).
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float nodeRadiusGraphSpace = nodeSize * u_correctionRatio / u_sizeRatio * 2.0;
  float nodeRadiusPixels = nodeRadiusGraphSpace * matrixScaleX * u_resolution.x / 2.0;

  // CSS-px inputs -> physical px, scaled by the zoom-dependent label ratio, so
  // the attachment stays glued to the label box exactly as the label scales.
  float zoomScale = u_zoomLabelSizeRatio;
  vec2 labelHalf = vec2(a_labelWidth, a_labelHeight) * 0.5 * zoomScale * u_pixelRatio;
  vec2 attachHalf = a_attachmentSize * 0.5 * zoomScale * u_pixelRatio;
  float gap = `).concat(Ge.toFixed(1),` * zoomScale * u_pixelRatio;
  float labelMargin = u_labelMargin * zoomScale * u_pixelRatio;

  // Graph-aligned labels add the camera angle so the attachment orbits with the box.
  mat2 labelRotMat = rotate2D(a_labelAngle - labelRotation * u_cameraAngle);

  // Label box center relative to the node center (pre-rotation). The shape-aware
  // edge distance comes from the frame texture, so placement matches the label.
  vec2 boxCenter = vec2(0.0);
  if (a_positionMode < 4.0) {
    float labelStart = nodeRadiusPixels * edgeDist + labelMargin;
    float textHalf = a_textHeight * 0.5 * zoomScale * u_pixelRatio;
    boxCenter = labelBoxCenter(a_positionMode, labelStart, labelHalf, textHalf);
  }

  // Horizontal anchor of below/above attachments tracks the label position, so
  // the attachment hangs from the label edge nearest the node (or is centered
  // when the label itself is node-centered): right->left, left->right, else center.
  float anchorX = 0.0;
  if (a_positionMode < 0.5) anchorX = -labelHalf.x + attachHalf.x;       // right label
  else if (a_positionMode < 1.5) anchorX = labelHalf.x - attachHalf.x;   // left label

  // Attachment center relative to the box (pre-rotation, Y-down). This offset
  // depends only on the box, the gap and the attachment size \u2014 never the shape.
  vec2 attachCenter;
  if (a_attachmentPlacement < 0.5) {
    // below
    attachCenter = boxCenter + vec2(anchorX, labelHalf.y + gap + attachHalf.y);
  } else if (a_attachmentPlacement < 1.5) {
    // above
    attachCenter = boxCenter + vec2(anchorX, -(labelHalf.y + gap + attachHalf.y));
  } else if (a_attachmentPlacement < 2.5) {
    // left, top-aligned
    attachCenter = boxCenter + vec2(-(labelHalf.x + gap + attachHalf.x), -labelHalf.y + attachHalf.y);
  } else {
    // right, top-aligned
    attachCenter = boxCenter + vec2(labelHalf.x + gap + attachHalf.x, -labelHalf.y + attachHalf.y);
  }

  // Rotate the whole assembly by the label angle, around the node center.
  vec2 rotatedCenter = labelRotMat * attachCenter;
  vec2 cornerOffset = labelRotMat * (a_quadCorner * attachHalf);

  // Node center in screen px (Y-down).
  vec2 nodeScreen = vec2(
    (nodeClip.x + 1.0) * u_resolution.x,
    (1.0 - nodeClip.y) * u_resolution.y
  ) * 0.5;

  // Snap node center to the pixel grid so label/backdrop/attachment move as one.
  vec2 snapDelta = (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

  // Snap the quad's top-left to integer pixels so atlas texels map 1:1.
  vec2 centerScreen = nodeScreen + rotatedCenter + snapDelta;
  vec2 topLeft = centerScreen - attachHalf;
  topLeft = mix(topLeft, round(topLeft), u_labelPixelSnapping);
  centerScreen = topLeft + attachHalf;

  vec2 vertexScreen = centerScreen + cornerOffset;
  gl_Position = vec4(
    vertexScreen.x * 2.0 / u_resolution.x - 1.0,
    1.0 - vertexScreen.y * 2.0 / u_resolution.y,
    0.0, 1.0
  );

  vec2 texOrigin = a_atlasRect.xy / u_atlasSize;
  vec2 texSize = a_atlasRect.zw / u_atlasSize;
  vec2 uv = (a_quadCorner + 1.0) / 2.0;
  v_texCoord = texOrigin + uv * texSize;
}
`);return a}var yl=`#version 300 es
precision highp float;

uniform sampler2D u_atlasTexture;

in vec2 v_texCoord;

layout(location = 0) out vec4 fragColor;
#ifdef PICKING_MODE
layout(location = 1) out vec4 pickColor;
#endif

void main() {
  // Canvas textures are premultiplied; output directly for (ONE, 1-SRC_ALPHA) blending
  vec4 color = texture(u_atlasTexture, v_texCoord);
  if (color.a < 0.01) discard;
  fragColor = color;
#ifdef PICKING_MODE
  pickColor = vec4(0.0); // Attachments are not pickable
#endif
}
`;function xl(a,n,t,e){var r,i,o=e.label,s=o===void 0?{}:o,l=(r=s.margin)!==null&&r!==void 0?r:dt,u=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},d=bl(),c=yl,f=function(h){function g(){var m;Y(this,g);for(var p=arguments.length,v=new Array(p),b=0;b<p;b++)v[b]=arguments[b];return m=te(this,g,[].concat(v)),S(m,"totalCount",0),S(m,"bufferCapacity",0),m}return ne(g,h),K(g,[{key:"getDefinition",value:function(){var p=WebGL2RenderingContext,v=p.FLOAT,b=p.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:d,FRAGMENT_SHADER_SOURCE:c,METHOD:b,UNIFORMS:["u_matrix","u_resolution","u_labelPixelSnapping","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_pixelRatio","u_labelMargin","u_zoomLabelSizeRatio","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth","u_atlasTexture"],ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:v},{name:"a_atlasRect",size:4,type:v},{name:"a_attachmentSize",size:2,type:v},{name:"a_positionMode",size:1,type:v},{name:"a_attachmentPlacement",size:1,type:v},{name:"a_labelWidth",size:1,type:v},{name:"a_labelHeight",size:1,type:v},{name:"a_textHeight",size:1,type:v},{name:"a_labelAngle",size:1,type:v}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:v}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"processAttachment",value:function(p,v){var b=this.floats,y=p*this.STRIDE;b[y++]=v.nodeIndex,b[y++]=v.atlasX,b[y++]=v.atlasY,b[y++]=v.atlasW,b[y++]=v.atlasH,b[y++]=v.attachWidth,b[y++]=v.attachHeight,b[y++]=v.positionMode,b[y++]=v.attachmentPlacement,b[y++]=v.labelWidth,b[y++]=v.labelHeight,b[y++]=v.textHeight,b[y++]=v.labelAngle}},{key:"setUniforms",value:function(p,v){var b=v.gl,y=v.uniformLocations;b.uniformMatrix3fv(y.u_matrix,!1,p.matrix),b.uniform2f(y.u_resolution,p.width*p.pixelRatio,p.height*p.pixelRatio),b.uniform1f(y.u_labelPixelSnapping,p.labelPixelSnapping),b.uniform1f(y.u_sizeRatio,p.sizeRatio),b.uniform1f(y.u_correctionRatio,p.correctionRatio),b.uniform1f(y.u_cameraAngle,p.cameraAngle),b.uniform1f(y.u_pixelRatio,p.pixelRatio),b.uniform1f(y.u_labelMargin,g.labelMargin),b.uniform1f(y.u_zoomLabelSizeRatio,1/u(p.zoomRatio)),b.uniform1i(y.u_nodeDataTexture,p.nodeDataTextureUnit),b.uniform1i(y.u_nodeDataTextureWidth,p.nodeDataTextureWidth),b.uniform1i(y.u_nodeFrameTexture,p.nodeFrameTextureUnit),b.uniform1i(y.u_nodeFrameTextureWidth,p.nodeFrameTextureWidth),b.uniform1i(y.u_atlasTexture,It)}},{key:"reallocateAttachments",value:function(p){this.totalCount=p,p>this.bufferCapacity&&(this.bufferCapacity=Math.max(p,Math.ceil(this.bufferCapacity*1.5)||10),ie(g,"reallocate",this,3)([this.bufferCapacity]))}},{key:"hasNothingToRender",value:function(){return this.totalCount===0}},{key:"drawWebGL",value:function(p,v){var b=v.gl;this.totalCount!==0&&b.drawArraysInstanced(p,0,this.VERTICES,this.totalCount)}}])}(He);return S(f,"labelMargin",l),new f(a,n,t)}var Ie=5;function An(a,n){return[].concat($(n),$(a.map(function(t){var e;return{attributes:(e=t.attributes)!==null&&e!==void 0?e:[]}})))}function ht(a,n){var t=me(An(a,n)),e=new Set(a.flatMap(function(u){var d;return(d=u.attributes)!==null&&d!==void 0?d:[]}).map(function(u){return u.name.replace(/^a_/,"")})),r={},i={},o=M(e),s;try{for(o.s();!(s=o.n()).done;){var l=s.value;r[l]=t.offsets[l],i[l]=t.specs[l]}}catch(u){o.e(u)}finally{o.f()}return B(B({},t),{},{offsets:r,specs:i})}function _l(a,n){var t=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_pickingPadding","u_nodeDataTexture","u_layerAttributeTexture"]),e=new Set,r=a.flatMap(function(h){return h.uniforms}).filter(function(h){return t.has(h.name)||e.has(h.name)?!1:(e.add(h.name),!0)}).map(function(h){return"uniform ".concat(h.type," ").concat(h.name,";")}).join(`
`),i=n.flatMap(function(h){return h.uniforms}).filter(function(h){return t.has(h.name)||e.has(h.name)?!1:(e.add(h.name),!0)}).map(function(h){return"uniform ".concat(h.type," ").concat(h.name,";")}).join(`
`),o=An(a,n),s=new Set,l=o.flatMap(function(h){return h.attributes}).filter(function(h){var g=h.name.replace(/^a_/,"");return s.has(g)?!1:(s.add(g),!0)}).map(function(h){var g=h.name.replace(/^a_/,""),m=h.size===1?"float":"vec".concat(h.size);return"out ".concat(m," v_").concat(g,";")}).join(`
`),u=lt(me(o),{varPrefix:"layer",baseTexelExpr:"nodeIdx * u_layerAttributeTexelsPerNode",textureWidthUniform:"u_layerAttributeTextureWidth",textureSamplerUniform:"u_layerAttributeTexture"}),d=u.fetchCode,c=u.varyingAssignments,f=`#version 300 es

// Standard node attributes (per instance) - minimal buffer usage
in float a_nodeIndex;  // Index into node data texture AND layer attribute texture
in vec4 a_id;          // Node ID for picking
in float a_opacity;    // Node opacity, applied once to the final fragment

// Constant attributes (per vertex, same for all instances)
in vec2 a_quadCorner;  // (-1,-1), (1,-1), (1,1), (-1,1) for quad corners

// Standard uniforms
uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;

// Layer attribute texture uniforms
uniform sampler2D u_layerAttributeTexture;
uniform int u_layerAttributeTextureWidth;
uniform int u_layerAttributeTexelsPerNode;

`.concat(r,`
`).concat(i,`

// Standard varyings
out vec2 v_uv;                    // Normalized coordinates [-1, 1]
out vec4 v_id;
out float v_opacity;
out float v_antialiasingWidth;    // Width for antialiasing in UV space
out float v_pixelSize;            // Node size in pixels (for pixel-mode borders)
out float v_pixelToUV;            // Conversion factor: multiply by this to convert screen pixels to UV units
out float v_shapeId;              // Shape ID for multi-shape programs

// Layer varyings
`).concat(l,`

// Node-data fetch helpers (geometry texel + rotation-flags texel)
`).concat(Le,`
`).concat(Ue,`

void main() {
  // Fetch node geometry: vec4(x, y, size, shapeId).
  int nodeIdx = int(a_nodeIndex);

  // Hidden nodes are flagged with a negative row by NodeProgram.process(). Push
  // the whole quad outside the clip volume: every vertex lands at the same
  // out-of-range position, so the primitive is fully clipped and rasterizes
  // nothing \u2014 neither to the frame buffer nor to the picking buffer.
  if (nodeIdx < 0) {
    gl_Position = vec4(2.0, 0.0, 0.0, 1.0);
    v_id = vec4(0.0);
    return;
  }

  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 a_position = nodeData.xy;
  float a_size = nodeData.z;
  v_shapeId = nodeData.w;  // Pass shape ID to fragment shader

  // Per-node rotation alignment: 0 = viewport (screen-upright), 1 = graph.
  float nodeRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).r;

`).concat(d,`

  // Calculate the actual size in pixels
  float size = a_size * u_correctionRatio / u_sizeRatio * 2.0;

  // In PICKING_MODE, inflate the quad by nodePickingPadding pixels on each side
  #ifdef PICKING_MODE
    float paddedSize = size + u_pickingPadding * u_correctionRatio;
    vec2 offset = a_quadCorner * paddedSize;
  #else
    vec2 offset = a_quadCorner * size;
  #endif
  // Counter-rotate the quad offset so viewport-aligned nodes stay upright as the
  // camera turns. Graph-aligned nodes (nodeRotation=1) skip it and turn with the
  // camera. The angle scales by (1 - nodeRotation) so both fall out of one path.
  {
    float ca = u_cameraAngle * (1.0 - nodeRotation);
    float c = cos(ca);
    float s = sin(ca);
    offset = mat2(c, s, -s, c) * offset;
  }
  vec2 position = a_position + offset;

  gl_Position = vec4(
    (u_matrix * vec3(position, 1)).xy,
    0,
    1
  );

  // In PICKING_MODE, UV is scaled beyond [-1, 1] to match the inflated quad
  #ifdef PICKING_MODE
    v_uv = a_quadCorner * (paddedSize / size);
  #else
    v_uv = a_quadCorner;
  #endif

  // Pass ID to fragment shader
  v_id = a_id;
  v_opacity = a_opacity;

  // Pass pixel size for layers that need pixel-mode calculations
  // Multiply by 2 because 'size' is half-width (offset from center), not full diameter
  v_pixelSize = size * 2.0;

  // Conversion factor from screen pixels to UV units
  // Same derivation as v_antialiasingWidth which represents ~1 pixel in UV space
  // P pixels in UV space = P * u_correctionRatio / size
  v_pixelToUV = u_correctionRatio / size;

  // We use an antialiasing width of 1px (so v_pixelToUV)
  v_antialiasingWidth = v_pixelToUV;

  // Pass layer attributes to fragment shader (fetched from texture)
`).concat(c,`
}
`);return f}function Tl(a,n,t){var e=arguments.length>3&&arguments[3]!==void 0?arguments[3]:!0,r=n.map(function(g,m){var p="layer_".concat(g.name),v=[].concat($(g.attributes.map(function(b){return"v_".concat(b.name.replace(/^a_/,""))})),$(g.uniforms.map(function(b){return b.name}))).join(", ");return"  // Layer ".concat(m+1,": ").concat(g.name,`
  color = blendOver(color, `).concat(p,"(").concat(v,"));")}).join(`

`),i=new Set(["u_correctionRatio"]),o=new Set,s=a.flatMap(function(g){return g.uniforms}).filter(function(g){return i.has(g.name)||o.has(g.name)?!1:(o.add(g.name),!0)}).map(function(g){return"uniform ".concat(g.type," ").concat(g.name,";")}).join(`
`),l=n.flatMap(function(g){return g.uniforms}).filter(function(g){return i.has(g.name)||o.has(g.name)?!1:(o.add(g.name),!0)}).map(function(g){return"uniform ".concat(g.type," ").concat(g.name,";")}).join(`
`),u=new Set,d=An(a,n).flatMap(function(g){return g.attributes}).filter(function(g){var m=g.name.replace(/^a_/,"");return u.has(m)?!1:(u.add(m),!0)}).map(function(g){var m=g.name.replace(/^a_/,""),p=g.size===1?"float":"vec".concat(g.size);return"in ".concat(p," v_").concat(m,";")}).join(`
`),c=ca(a),f=ol(a,t),h=`#version 300 es
precision highp float;

// Standard varyings
in vec2 v_uv;
in vec4 v_id;
in float v_opacity;
in float v_antialiasingWidth;
in float v_pixelSize;
in float v_pixelToUV;
in float v_shapeId;  // Shape ID for multi-shape programs

// Standard uniforms (needed for some layer calculations like pixel-mode borders)
uniform float u_correctionRatio;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif

// Shape uniforms
`.concat(s,`

// Layer uniforms
`).concat(l,`

// Layer varyings
`).concat(d,`

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

// LayerContext struct - provides rendering context to all layers
struct LayerContext {
  float sdf;             // Signed distance from shape boundary (negative inside)
  vec2 uv;               // UV coordinates [-1, 1], center at (0,0)
  float shapeSize;       // Effective shape size (~diameter) in UV space (1.0 - aaWidth)
  float shapeHalfSize;   // Effective shape half size (~radius) in UV space
  float pixelSize;       // Node full size (~diameter) in screen pixels
  float aaWidth;         // Anti-aliasing width for smooth transitions
  float correctionRatio; // Scaling factor for consistent rendering across zoom levels
  float pixelToUV;       // Conversion factor: multiply screen pixels by this to get UV units
  float inradiusFactor;  // Ratio of inradius to circumradius (shape depth factor)
};

LayerContext context;  // Global instance, populated before layer calls

// Alpha "over" compositing for layer blending
vec4 blendOver(vec4 bg, vec4 fg) {
  float a = fg.a;
  return vec4(mix(bg.rgb, fg.rgb, a), bg.a + a * (1.0 - bg.a));
}

// SDF shape functions
`).concat(c,`

// Shape selector function (sets context.sdf and context.inradiusFactor)
`).concat(f,`

// Layer functions
`).concat(n.map(function(g){return g.glsl}).join(`

`),`

void main() {
  // 1. Setup LayerContext (available to all layer functions)
  context.shapeSize = 1.0 - v_antialiasingWidth;
  context.shapeHalfSize = context.shapeSize * 0.5;
  context.pixelSize = v_pixelSize;
  context.uv = v_uv;
  context.aaWidth = v_antialiasingWidth;
  context.correctionRatio = u_correctionRatio;
  context.pixelToUV = v_pixelToUV;

  // Query shape SDF based on shapeId (sets context.sdf and context.inradiusFactor)
  queryNodeSDF(int(v_shapeId), v_uv, context.shapeSize);

  // 2. Early discard for pixels fully outside the shape (with AA margin)
  // In PICKING_MODE, allow extra fragments up to the picking padding distance
  #ifdef PICKING_MODE
    if (context.sdf > u_pickingPadding * v_pixelToUV + context.aaWidth) discard;
  #else
    if (context.sdf > context.aaWidth) discard;
  #endif

  // 3. Apply layers sequentially with "over" compositing
  vec4 color = vec4(0.0);

`).concat(r,`

  #ifdef PICKING_MODE
    // Picking pass: output node ID for pixels within the picking area.
    if (context.sdf > u_pickingPadding * v_pixelToUV) discard;
    fragColor = v_id;
  #else
`).concat(e?`    // Visual pass: apply antialiasing at shape boundary, node opacity once
    // smoothstep provides smooth transition from opaque to transparent
    float alpha = smoothstep(context.aaWidth, -context.aaWidth, context.sdf) * v_opacity;`:`    // Visual pass: hard-edged (no anti-aliasing gradient) shape boundary, node opacity applied once
    float alpha = (context.sdf < 0.0 ? 1.0 : 0.0) * v_opacity;`,`
    // Mix with transparent to fade both color AND alpha together (avoids bright halo)
    fragColor = mix(vec4(0.0), color, alpha);
  #endif
}
`);return h}function Sl(a,n){var t=new Set;return t.add("u_matrix"),t.add("u_sizeRatio"),t.add("u_correctionRatio"),t.add("u_cameraAngle"),t.add("u_pickingPadding"),t.add("u_nodeDataTexture"),t.add("u_nodeDataTextureWidth"),t.add("u_layerAttributeTexture"),t.add("u_layerAttributeTextureWidth"),t.add("u_layerAttributeTexelsPerNode"),a.forEach(function(e){e.uniforms.forEach(function(r){return t.add(r.name)})}),n.forEach(function(e){e.uniforms.forEach(function(r){return t.add(r.name)})}),Array.from(t)}function El(a){var n=WebGL2RenderingContext,t=n.UNSIGNED_BYTE,e=n.FLOAT;return[{name:"a_nodeIndex",size:1,type:e},{name:"a_id",size:4,type:t,normalized:!0},{name:"a_opacity",size:1,type:e}]}function Ir(a){var n=a.shapes,t=a.layers,e=a.shapeGlobalIds,r=a.antialias,i=r===void 0?!0:r;return{vertexShader:_l(n,t),fragmentShader:Tl(n,t,e,i),uniforms:Sl(n,t),attributes:El()}}function Zr(a,n,t){var e=ht(a,n),r=e.specs;return Object.keys(r).map(function(i){return"flat ".concat(t," ").concat(r[i].size===1?"float":"vec".concat(r[i].size)," v_").concat(i,";")}).join(`
`)}function Rl(a){var n,t,e=a.shapes,r=a.layers,i=a.shapeGlobalIds,o=lt(ht(e,r),{varPrefix:"nodeAttr",baseTexelExpr:"nodeIdx * u_layerAttributeTexelsPerNode",textureWidthUniform:"u_layerAttributeTextureWidth",textureSamplerUniform:"u_layerAttributeTexture"}),s=e.length===1?"float inradiusFactor = ".concat(ae((n=e[0].inradiusFactor)!==null&&n!==void 0?n:1),";"):"float inradiusFactor = ".concat(ae((t=e[0].inradiusFactor)!==null&&t!==void 0?t:1),`;
  switch (int(shapeId)) {
`).concat(e.map(function(u,d){var c,f=i?i[d]:d;return"    case ".concat(f,": inradiusFactor = ").concat(ae((c=u.inradiusFactor)!==null&&c!==void 0?c:1),"; break;")}).join(`
`),`
    default: break;
  }`),l=`#version 300 es

in float a_nodeIndex;
in float a_labelWidth;
in float a_labelHeight;
in float a_textHeight;
in float a_positionMode;
in float a_labelAngle;
in vec4 a_backdropColor;
in vec4 a_backdropShadowColor;
in float a_backdropShadowBlur;
in float a_backdropPadding;
in vec4 a_backdropBorderColor;
in vec4 a_backdropExtra; // [borderWidth, cornerRadius, labelPadding, area]
in vec2 a_labelBoxOffset;
in vec2 a_quadCorner;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform float u_pixelRatio;
uniform float u_labelMargin;
uniform float u_zoomLabelSizeRatio;
uniform float u_labelPixelSnapping;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;
uniform sampler2D u_layerAttributeTexture;
uniform int u_layerAttributeTextureWidth;
uniform int u_layerAttributeTexelsPerNode;

out vec2 v_uv;
out vec2 v_nodeCenter;
out float v_nodeRadius;
out vec2 v_labelCenter;
out vec2 v_labelHalfSize;
out float v_aaWidth;
out float v_shapeId;
out float v_nodeRotation;
out float v_labelAngle;
out vec4 v_backdropColor;
out vec4 v_backdropShadowColor;
out float v_backdropShadowBlur;
out float v_backdropPadding;
out vec4 v_backdropBorderColor;
out float v_backdropBorderWidth;
out float v_backdropCornerRadius;
out float v_backdropArea;
`.concat(Zr(e,r,"out"),`

`).concat(Le,`
`).concat(Ue,`
`).concat(ct,`

void main() {
  int nodeIdx = int(a_nodeIndex);
`).concat(o.fetchCode,`
`).concat(o.varyingAssignments,`

  // Node data: (x, y, size, shapeId). shapeId (global) is forwarded to the
  // fragment shader, which keeps the shape SDF for the outline.
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 nodePosition = nodeData.xy;
  float nodeSize = nodeData.z;
  float shapeId = nodeData.w;

  // Per-node rotation alignment (0 = viewport, 1 = graph). nodeRotation drives
  // the fragment's shape outline; labelRotation turns the label box with camera.
  vec4 nodeFlags = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  float nodeRotation = nodeFlags.r;
  float labelRotation = nodeFlags.g;
  v_nodeRotation = nodeRotation;

  `).concat(Xr,`
  // CSS pixel attributes are multiplied by u_pixelRatio to match nodeRadiusPixels,
  // which is already in physical pixels (nodeRadiusNDC * u_resolution.x / 2.0).
  float padding = a_backdropPadding * u_pixelRatio;
  float shadowBlur = a_backdropShadowBlur * u_pixelRatio;
  // Unpack a_backdropExtra: [borderWidth, cornerRadius, labelPadding, area]
  float borderWidth = a_backdropExtra.x * u_pixelRatio;
  float cornerRadius = a_backdropExtra.y * u_pixelRatio;
  float labelPad = a_backdropExtra.z * u_pixelRatio;
  float backdropArea = a_backdropExtra.w;
  // Use 2x shadowBlur so the Gaussian fully decays before the quad edge
  float totalExpansion = shadowBlur * 2.0 + borderWidth;
  float enlargedRadius = nodeRadiusPixels + padding;

  // Circumscribed radius for the quad bounds. Non-circular shapes reach past
  // their inradius out to their circumradius (= enlargedRadius / inradiusFactor),
  // in any direction once rotated. The axis-aligned quad must contain that, or
  // the fill/shadow gets clipped (square corners, triangle tip, etc.).
  `).concat(s,`
  float boundRadius = enlargedRadius / inradiusFactor;

  // Apply zoom-dependent label size scaling
  float zoomScale = u_zoomLabelSizeRatio;
  float labelW = a_labelWidth * zoomScale * u_pixelRatio;
  float labelH = a_labelHeight * zoomScale * u_pixelRatio;
  float labelMargin = u_labelMargin * zoomScale * u_pixelRatio;

  // Only apply labelPad when a label is actually present
  float effectiveLabelPad = labelW > 0.0 ? labelPad : 0.0;
  vec2 labelHalfSize = vec2(labelW * 0.5 + effectiveLabelPad, labelH * 0.5 + effectiveLabelPad);
  vec2 labelOffset = vec2(0.0);

  // Effective label angle: intrinsic angle plus the camera angle when the label
  // is graph-aligned, so the box orbits the node in lockstep with the frame-pass.
  float labelAngle = a_labelAngle - labelRotation * u_cameraAngle;
  float la_c = cos(labelAngle);
  float la_s = sin(labelAngle);
  mat2 labelRotMat = mat2(la_c, -la_s, la_s, la_c);

  vec3 nodeClip = u_matrix * vec3(nodePosition, 1.0);
  vec2 snapDelta = vec2(0.0);

  if (labelW > 0.0) {
    // labelW > 0.0 means this node's label is displayed, so the frame-pass wrote
    // its edge distance this frame.
    float edgeDistPixels = nodeRadiusPixels * readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;
    // labelMargin matches the label shader's margin (gap from node edge to text)
    float labelStart = edgeDistPixels + labelMargin;
    // Above/below center on the actual glyph height, not the font line box, so
    // the box stays aligned with the rendered text (matches labelBoxCenter()).
    float textHalf = a_textHeight * zoomScale * u_pixelRatio * 0.5;

    // Snap node center to pixel grid so label/backdrop/attachment move as a unit
    vec2 nodeScreen = vec2(
      (nodeClip.x + 1.0) * u_resolution.x,
      (1.0 - nodeClip.y) * u_resolution.y
    ) * 0.5;
    snapDelta = (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

    if (a_positionMode < 0.5) {
      // Right: box spans from node center to text end + padding
      float boxRightEdge = labelStart + labelW + labelPad;
      labelOffset = vec2(boxRightEdge * 0.5, 0.0);
      labelHalfSize.x = boxRightEdge * 0.5;
    } else if (a_positionMode < 1.5) {
      // Left: mirror of right
      float boxLeftEdge = labelStart + labelW + labelPad;
      labelOffset = vec2(-boxLeftEdge * 0.5, 0.0);
      labelHalfSize.x = boxLeftEdge * 0.5;
    } else if (a_positionMode < 2.5) {
      // Above: text bottom at labelStart, centered horizontally
      labelOffset = vec2(0.0, -(labelStart + textHalf));
    } else if (a_positionMode < 3.5) {
      // Below: text top at labelStart, centered horizontally
      labelOffset = vec2(0.0, labelStart + textHalf);
    }
    // over (>=4): labelOffset stays (0,0) \u2014 text centered on the node.

    // The attachment-cover shift is in label space (like the attachment itself),
    // so rotate it together with the position offset \u2014 otherwise the box drifts
    // off the attachment as the label angle grows.
    labelOffset = labelRotMat * (labelOffset + a_labelBoxOffset * zoomScale * u_pixelRatio);
  }

  // For node-only mode, zero out label dimensions
  if (backdropArea > 0.5 && backdropArea < 1.5) {
    labelHalfSize = vec2(0.0);
    labelOffset = vec2(0.0);
  }

  vec2 minBound, maxBound;

  bool hasLabelBounds = labelW > 0.0 && (backdropArea > 1.5 || backdropArea < 0.5);

  if (hasLabelBounds) {
    // Union with label bounds (area=both) or label-only bounds (area=label)
    vec2 labelMin, labelMax;

    if (a_labelAngle != 0.0) {
      vec2 corner1 = labelOffset + labelRotMat * vec2(-labelHalfSize.x, -labelHalfSize.y);
      vec2 corner2 = labelOffset + labelRotMat * vec2(labelHalfSize.x, -labelHalfSize.y);
      vec2 corner3 = labelOffset + labelRotMat * vec2(labelHalfSize.x, labelHalfSize.y);
      vec2 corner4 = labelOffset + labelRotMat * vec2(-labelHalfSize.x, labelHalfSize.y);
      labelMin = min(min(corner1, corner2), min(corner3, corner4));
      labelMax = max(max(corner1, corner2), max(corner3, corner4));
    } else {
      labelMin = labelOffset - labelHalfSize;
      labelMax = labelOffset + labelHalfSize;
    }

    if (backdropArea > 1.5) {
      // Label-only: bounds from label rect only
      minBound = labelMin - totalExpansion;
      maxBound = labelMax + totalExpansion;
    } else {
      // Both: union of node + label
      minBound = min(-vec2(boundRadius), labelMin) - totalExpansion;
      maxBound = max(vec2(boundRadius), labelMax) + totalExpansion;
    }
  } else {
    // Node-only or no visible label
    float totalRadius = boundRadius + totalExpansion;
    minBound = -vec2(totalRadius);
    maxBound = vec2(totalRadius);
  }

  vec2 quadSize = maxBound - minBound;
  vec2 quadCenter = (minBound + maxBound) * 0.5;

  vec2 localPos = quadCenter + a_quadCorner * quadSize * 0.5 + snapDelta;
  vec2 ndcOffset = localPos * 2.0 / u_resolution;
  ndcOffset.y = -ndcOffset.y;

  gl_Position = vec4(nodeClip.xy + ndcOffset, 0.0, 1.0);

  v_uv = localPos;
  v_nodeCenter = vec2(0.0);
  v_nodeRadius = nodeRadiusPixels;
  v_labelCenter = labelOffset;
  v_labelHalfSize = labelHalfSize;
  v_aaWidth = 1.0;
  v_shapeId = shapeId;
  v_labelAngle = labelAngle;
  v_backdropColor = a_backdropColor;
  v_backdropShadowColor = a_backdropShadowColor;
  v_backdropShadowBlur = a_backdropShadowBlur;
  v_backdropPadding = a_backdropPadding;
  v_backdropBorderColor = a_backdropBorderColor;
  v_backdropBorderWidth = borderWidth;
  v_backdropCornerRadius = cornerRadius;
  v_backdropArea = backdropArea;
}
`);return l}function Al(a){var n=a.shapes,t=a.layers,e=a.shapeGlobalIds,r=ca(n),i=Ft(n).map(function(f){return"uniform ".concat(f.type," ").concat(f.name,";")}).join(`
`),o=function(h){return _n(h,"nodeUV","1.0")},s;if(n.length===1)s="float nodeSdfNormalized = ".concat(o(n[0]),";");else{var l=n.map(function(f,h){var g=e?e[h]:h;return"    case ".concat(g,": nodeSdfNormalized = ").concat(o(f),"; break;")}).join(`
`),u=o(n[0]);s=`float nodeSdfNormalized;
  int shapeId = int(v_shapeId);
  switch (shapeId) {
`.concat(l,`
    default: nodeSdfNormalized = `).concat(u,`;
  }`)}var d=`float effectiveRadius = max(enlargedRadius - cornerRadius, 0.01);
  float ca = u_cameraAngle * v_nodeRotation;
  float ca_c = cos(ca);
  float ca_s = sin(ca);
  vec2 rotatedScreenUV = mat2(ca_c, -ca_s, ca_s, ca_c) * screenUV;
  vec2 nodeUV = vec2(rotatedScreenUV.x, -rotatedScreenUV.y) / effectiveRadius;`,c=`#version 300 es
precision highp float;

in vec2 v_uv;
in vec2 v_nodeCenter;
in float v_nodeRadius;
in vec2 v_labelCenter;
in vec2 v_labelHalfSize;
in float v_aaWidth;
in float v_shapeId;
in float v_nodeRotation;
in float v_labelAngle;
in vec4 v_backdropColor;
in vec4 v_backdropShadowColor;
in float v_backdropShadowBlur;
in float v_backdropPadding;
in vec4 v_backdropBorderColor;
in float v_backdropBorderWidth;
in float v_backdropCornerRadius;
in float v_backdropArea;
`.concat(Zr(n,t,"in"),`

uniform float u_cameraAngle;
`).concat(i,`

layout(location = 0) out vec4 fragColor;
layout(location = 1) out vec4 fragPicking;

`).concat(r,`
`).concat(ll,`
`).concat(ul,`
`).concat(dl,`
`).concat(cl,`

void main() {
  vec4 backdropColor = v_backdropColor;
  vec4 shadowColor = v_backdropShadowColor;
  float shadowBlur = v_backdropShadowBlur;
  float padding = v_backdropPadding;
  vec4 borderColor = v_backdropBorderColor;
  float borderWidth = v_backdropBorderWidth;
  float cornerRadius = v_backdropCornerRadius;

  float enlargedRadius = v_nodeRadius + padding;
  vec2 screenUV = v_uv - v_nodeCenter;
  `).concat(d,`

  // Query the correct shape SDF based on shapeId
  `).concat(s,`
  float nodeSdfPixels = nodeSdfNormalized * effectiveRadius - cornerRadius;

  // Label SDF with optional corner radius and rotation
  float labelSdfPixels;
  if (v_labelHalfSize.x > 0.0) {
    vec2 labelP = v_uv - v_labelCenter;
    labelSdfPixels = sdfRoundedRotatedBox(labelP, v_labelHalfSize, v_labelAngle, cornerRadius);
  } else {
    labelSdfPixels = 10000.0;
  }

  // Select area: 0=both, 1=node, 2=label
  float combinedSdf;
  if (v_backdropArea > 1.5) {
    combinedSdf = labelSdfPixels;
  } else if (v_backdropArea > 0.5) {
    combinedSdf = nodeSdfPixels;
  } else {
    combinedSdf = min(nodeSdfPixels, labelSdfPixels);
  }

  // Fill + border composite
  float outerEdge = smoothstep(v_aaWidth, -v_aaWidth, combinedSdf);
  vec4 background;
  if (borderWidth > 0.5) {
    float innerEdge = smoothstep(v_aaWidth, -v_aaWidth, combinedSdf + borderWidth);
    float fillAlpha = innerEdge * backdropColor.a;
    vec4 fill = vec4(backdropColor.rgb * fillAlpha, fillAlpha);
    float borderAlpha = (outerEdge - innerEdge) * borderColor.a;
    vec4 border = vec4(borderColor.rgb * borderAlpha, borderAlpha);
    background = fill + border * (1.0 - fill.a);
  } else {
    float fillAlpha = outerEdge * backdropColor.a;
    background = vec4(backdropColor.rgb * fillAlpha, fillAlpha);
  }

  // Gaussian-like shadow falloff (mimics canvas shadowBlur)
  vec4 shadow = vec4(0.0);
  float sigma = shadowBlur / 2.5;
  if (sigma > 0.001) {
    float shadowDist = max(0.0, combinedSdf);
    float shadowAlpha = exp(-(shadowDist * shadowDist) / (2.0 * sigma * sigma)) * shadowColor.a;
    shadow = vec4(shadowColor.rgb * shadowAlpha, shadowAlpha);
  }

  fragColor = background + shadow * (1.0 - background.a);
  fragPicking = vec4(0.0);
}
`);return c}function Dl(a){var n=["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_resolution","u_pixelRatio","u_labelMargin","u_zoomLabelSizeRatio","u_labelPixelSnapping","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth","u_layerAttributeTexture","u_layerAttributeTextureWidth","u_layerAttributeTexelsPerNode"],t=M(Ft(a)),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;n.includes(r.name)||n.push(r.name)}}catch(i){t.e(i)}finally{t.f()}return n}function wl(a){return{vertexShader:Rl(a),fragmentShader:Al(a),uniforms:Dl(a.shapes)}}function Ll(a,n,t,e){var r,i,o=e.label,s=o===void 0?{}:o,l=e.shapes,u=e.layers,d=e.getAttributeTexture,c=e.shapeGlobalIds;if(l.length===0)throw new Error("createBackdropProgram: at least one shape must be provided in 'shapes'");var f=(r=s.margin)!==null&&r!==void 0?r:5,h=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},g={shapes:l,layers:u,shapeGlobalIds:c},m=wl(g),p=function(v){function b(){var y;Y(this,b);for(var T=arguments.length,x=new Array(T),_=0;_<T;_++)x[_]=arguments[_];return y=te(this,b,[].concat(x)),S(y,"totalBackdropCount",0),S(y,"bufferCapacity",0),y}return ne(b,v),K(b,[{key:"getDefinition",value:function(){var T=WebGL2RenderingContext,x=T.FLOAT,_=T.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:m.vertexShader,FRAGMENT_SHADER_SOURCE:m.fragmentShader,METHOD:_,UNIFORMS:m.uniforms,ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:x},{name:"a_labelWidth",size:1,type:x},{name:"a_labelHeight",size:1,type:x},{name:"a_textHeight",size:1,type:x},{name:"a_positionMode",size:1,type:x},{name:"a_labelAngle",size:1,type:x},{name:"a_backdropColor",size:4,type:x},{name:"a_backdropShadowColor",size:4,type:x},{name:"a_backdropShadowBlur",size:1,type:x},{name:"a_backdropPadding",size:1,type:x},{name:"a_backdropBorderColor",size:4,type:x},{name:"a_backdropExtra",size:4,type:x},{name:"a_labelBoxOffset",size:2,type:x}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:x}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"processBackdrop",value:function(T,x){var _=this.floats,R=this.STRIDE,E=T*R;_[E++]=x.nodeIndex,_[E++]=x.labelWidth,_[E++]=x.labelHeight,_[E++]=x.textHeight,_[E++]=ut[x.position],_[E++]=x.labelAngle,_[E++]=x.backdropColor[0],_[E++]=x.backdropColor[1],_[E++]=x.backdropColor[2],_[E++]=x.backdropColor[3],_[E++]=x.backdropShadowColor[0],_[E++]=x.backdropShadowColor[1],_[E++]=x.backdropShadowColor[2],_[E++]=x.backdropShadowColor[3],_[E++]=x.backdropShadowBlur,_[E++]=x.backdropPadding,_[E++]=x.backdropBorderColor[0],_[E++]=x.backdropBorderColor[1],_[E++]=x.backdropBorderColor[2],_[E++]=x.backdropBorderColor[3],_[E++]=x.backdropBorderWidth,_[E++]=x.backdropCornerRadius,_[E++]=x.backdropLabelPadding,_[E++]=x.backdropArea,_[E++]=x.labelBoxOffset[0],_[E++]=x.labelBoxOffset[1]}},{key:"setUniforms",value:function(T,x){var _=x.gl,R=x.uniformLocations;_.uniformMatrix3fv(R.u_matrix,!1,T.matrix),_.uniform1f(R.u_sizeRatio,T.sizeRatio),_.uniform1f(R.u_correctionRatio,T.correctionRatio),_.uniform1f(R.u_cameraAngle,T.cameraAngle),_.uniform2f(R.u_resolution,T.width*T.pixelRatio,T.height*T.pixelRatio),_.uniform1f(R.u_pixelRatio,T.pixelRatio),_.uniform1f(R.u_labelMargin,b.labelMargin),_.uniform1f(R.u_zoomLabelSizeRatio,1/h(T.zoomRatio)),_.uniform1f(R.u_labelPixelSnapping,T.labelPixelSnapping),_.uniform1i(R.u_nodeDataTexture,T.nodeDataTextureUnit),_.uniform1i(R.u_nodeDataTextureWidth,T.nodeDataTextureWidth),_.uniform1i(R.u_nodeFrameTexture,T.nodeFrameTextureUnit),_.uniform1i(R.u_nodeFrameTextureWidth,T.nodeFrameTextureWidth);var E=d();R.u_layerAttributeTexture&&E&&(E.bind(Ie),_.uniform1i(R.u_layerAttributeTexture,Ie),_.uniform1i(R.u_layerAttributeTextureWidth,E.getTextureWidth()),_.uniform1i(R.u_layerAttributeTexelsPerNode,E.getTexelsPerItem()));var L=M(Ft(l)),D;try{for(L.s();!(D=L.n()).done;){var F=D.value;this.setTypedUniform(F,x)}}catch(A){L.e(A)}finally{L.f()}}},{key:"hasNothingToRender",value:function(){return this.totalBackdropCount===0}},{key:"drawWebGL",value:function(T,x){var _=x.gl;this.totalBackdropCount!==0&&(this.isInstanced?_.drawArraysInstanced(T,0,this.VERTICES,this.totalBackdropCount):_.drawArrays(T,0,this.totalBackdropCount*this.VERTICES))}},{key:"reallocate",value:function(T){this.totalBackdropCount=T,T>this.bufferCapacity&&(this.bufferCapacity=Math.max(T,Math.ceil(this.bufferCapacity*1.5)||10),ie(b,"reallocate",this,3)([this.bufferCapacity]))}}])}(He);return S(p,"labelMargin",f),new p(a,n,t)}var Qr=function(a){function n(){var t;Y(this,n);for(var e=arguments.length,r=new Array(e),i=0;i<e;i++)r[i]=arguments[i];return t=te(this,n,[].concat(r)),S(t,"totalCharacterCount",0),S(t,"bufferCapacity",0),t}return ne(n,a),K(n,[{key:"processLabel",value:function(e,r,i){if(i.hidden||!i.text)return 0;for(var o=i.text,s=o.length,l=0;l<s;l++){var u=o[l];this.processCharacter(r+l,i,u,l)}return s}},{key:"hasNothingToRender",value:function(){return this.totalCharacterCount===0}},{key:"drawWebGL",value:function(e,r){var i=r.gl;this.totalCharacterCount!==0&&(this.isInstanced?i.drawArraysInstanced(e,0,this.VERTICES,this.totalCharacterCount):i.drawArrays(e,0,this.totalCharacterCount*this.VERTICES))}},{key:"reallocate",value:function(e){this.totalCharacterCount=e,e>this.bufferCapacity&&(this.bufferCapacity=Math.max(e,Math.ceil(this.bufferCapacity*1.5)||1e3),ie(n,"reallocate",this,3)([this.bufferCapacity]))}}])}(He);function Cl(){var a=`#version 300 es

in float a_nodeIndex;
in vec4 a_id;
in vec4 a_color;
in float a_labelWidth;
in float a_labelHeight;
in float a_textHeight;
in float a_positionMode;
in float a_labelAngle;
in float a_padding;
in vec2 a_quadCorner;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform float u_pixelRatio;
uniform float u_labelMargin;
uniform float u_zoomLabelSizeRatio;
uniform float u_labelPixelSnapping;
uniform float u_pickingPadding;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;

out vec4 v_id;
out vec4 v_color;

`.concat(Le,`
`).concat(Ue,`
`).concat(ct,`
`).concat(qr,`

void main() {
  int nodeIdx = int(a_nodeIndex);

  // Node data: (x, y, size, shapeId).
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 nodePosition = nodeData.xy;
  float nodeSize = nodeData.z;

  // Shape-aware edge distance, read once from the shared frame texture.
  float edgeDist = readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;

  // Per-node label rotation alignment: 0 = viewport, 1 = label turns with camera.
  float labelRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).g;

  `).concat(Xr,`

  float zoomScale = u_zoomLabelSizeRatio;
  float labelW = a_labelWidth * zoomScale * u_pixelRatio;
  float labelH = a_labelHeight * zoomScale * u_pixelRatio;
  float labelMargin = u_labelMargin * zoomScale * u_pixelRatio;
#ifdef PICKING_MODE
  float padding = u_pickingPadding * u_pixelRatio;
#else
  float padding = a_padding * u_pixelRatio;
#endif

  if (labelW <= 0.0) {
    gl_Position = vec4(2.0, 0.0, 0.0, 1.0);
    v_id = vec4(0.0);
    v_color = vec4(0.0);
    return;
  }

  vec2 labelHalfSize = vec2(labelW * 0.5 + padding, labelH * 0.5 + padding);
  vec2 labelOffset = vec2(0.0);

  // Graph-aligned labels add the camera angle so the rect orbits with the text.
  float labelAngle = a_labelAngle - labelRotation * u_cameraAngle;
  float la_c = cos(labelAngle);
  float la_s = sin(labelAngle);
  mat2 labelRotMat = mat2(la_c, -la_s, la_s, la_c);

  vec3 nodeClip = u_matrix * vec3(nodePosition, 1.0);
  vec2 nodeScreen = vec2(
    (nodeClip.x + 1.0) * u_resolution.x,
    (1.0 - nodeClip.y) * u_resolution.y
  ) * 0.5;
  vec2 snapDelta = (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

  if (a_positionMode < 4.0) {
    float labelStart = nodeRadiusPixels * edgeDist + labelMargin;
    float textHalf = a_textHeight * zoomScale * u_pixelRatio * 0.5;
    // Box center uses the text half-size; the padding expands the quad below.
    labelOffset = labelRotMat * labelBoxCenter(a_positionMode, labelStart, vec2(labelW * 0.5, labelH * 0.5), textHalf);
  }

  // Rotate the rect with the label so it stays aligned with the (rotated) text.
  vec2 localPos = labelOffset + labelRotMat * (a_quadCorner * labelHalfSize);
  vec2 ndcOffset = (localPos + snapDelta) * 2.0 / u_resolution;
  ndcOffset.y = -ndcOffset.y;

  gl_Position = vec4(nodeClip.xy + ndcOffset, 0.0, 1.0);
  v_id = a_id;
  v_color = a_color;
}
`);return a}var Pl=`#version 300 es
precision highp float;

in vec4 v_id;
in vec4 v_color;

out vec4 fragColor;

void main() {
  #ifdef PICKING_MODE
    fragColor = v_id;
  #else
    if (v_color.a <= 0.0) discard;
    // v_color is non-premultiplied RGBA (0-1); convert to premultiplied for blending
    fragColor = vec4(v_color.rgb * v_color.a, v_color.a);
  #endif
}
`;function kl(a,n,t,e){var r,i,o=e.label,s=o===void 0?{}:o,l=(r=s.margin)!==null&&r!==void 0?r:dt,u=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},d=Cl(),c=function(f){function h(){var g;Y(this,h);for(var m=arguments.length,p=new Array(m),v=0;v<m;v++)p[v]=arguments[v];return g=te(this,h,[].concat(p)),S(g,"totalCount",0),S(g,"bufferCapacity",0),g}return ne(h,f),K(h,[{key:"getDefinition",value:function(){var m=WebGL2RenderingContext,p=m.FLOAT,v=m.UNSIGNED_BYTE,b=m.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:d,FRAGMENT_SHADER_SOURCE:Pl,METHOD:b,UNIFORMS:["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_resolution","u_pixelRatio","u_labelMargin","u_zoomLabelSizeRatio","u_labelPixelSnapping","u_pickingPadding","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth"],ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:p},{name:"a_id",size:4,type:v,normalized:!0},{name:"a_color",size:4,type:v,normalized:!0},{name:"a_labelWidth",size:1,type:p},{name:"a_labelHeight",size:1,type:p},{name:"a_textHeight",size:1,type:p},{name:"a_positionMode",size:1,type:p},{name:"a_labelAngle",size:1,type:p},{name:"a_padding",size:1,type:p}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:p}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"processLabelBackground",value:function(m,p){var v=this.floats,b=this.ints,y=m*this.STRIDE;v[y++]=p.nodeIndex,b[y++]=p.id,v[y++]=p.color,v[y++]=p.labelWidth,v[y++]=p.labelHeight,v[y++]=p.textHeight,v[y++]=p.positionMode,v[y++]=p.labelAngle,v[y++]=p.padding}},{key:"setUniforms",value:function(m,p){var v=p.gl,b=p.uniformLocations;v.uniformMatrix3fv(b.u_matrix,!1,m.matrix),v.uniform1f(b.u_sizeRatio,m.sizeRatio),v.uniform1f(b.u_correctionRatio,m.correctionRatio),v.uniform1f(b.u_cameraAngle,m.cameraAngle),v.uniform2f(b.u_resolution,m.width*m.pixelRatio,m.height*m.pixelRatio),v.uniform1f(b.u_pixelRatio,m.pixelRatio),v.uniform1f(b.u_labelMargin,h.labelMargin),v.uniform1f(b.u_zoomLabelSizeRatio,1/u(m.zoomRatio)),v.uniform1f(b.u_labelPixelSnapping,m.labelPixelSnapping),v.uniform1f(b.u_pickingPadding,m.labelPickingPadding),v.uniform1i(b.u_nodeDataTexture,m.nodeDataTextureUnit),v.uniform1i(b.u_nodeDataTextureWidth,m.nodeDataTextureWidth),v.uniform1i(b.u_nodeFrameTexture,m.nodeFrameTextureUnit),v.uniform1i(b.u_nodeFrameTextureWidth,m.nodeFrameTextureWidth)}},{key:"hasNothingToRender",value:function(){return this.totalCount===0}},{key:"drawWebGL",value:function(m,p){var v=p.gl;this.totalCount!==0&&v.drawArraysInstanced(v.TRIANGLE_STRIP,0,this.VERTICES,this.totalCount)}},{key:"reallocate",value:function(m){this.totalCount=m,m>this.bufferCapacity&&(this.bufferCapacity=Math.max(m,Math.ceil(this.bufferCapacity*1.5)||10),ie(h,"reallocate",this,3)([this.bufferCapacity]))}}])}(He);return S(c,"labelMargin",l),new c(a,n,t)}var Se={fontSize:64,buffer:8,radius:24,cutoff:.25,maxTextureSize:2048,debounceTimeout:100},wt=2,Ct=1e20;function Fl(a,n,t,e,r){var i=a+r*4,o=document.createElement("canvas");o.width=i,o.height=i;var s=o.getContext("2d",{willReadFrequently:!0});return s.font="".concat(e," ").concat(t," ").concat(a,"px ").concat(n),s.textBaseline="alphabetic",s.textAlign="left",s.fillStyle="black",{ctx:s,canvasSize:i,gridOuter:new Float64Array(i*i),gridInner:new Float64Array(i*i),f:new Float64Array(i),z:new Float64Array(i+1),v:new Uint16Array(i)}}function Il(a,n,t,e,r){var i=a.ctx,o=a.canvasSize,s=i.measureText(n),l=s.width,u=s.actualBoundingBoxAscent,d=s.actualBoundingBoxDescent,c=s.actualBoundingBoxLeft,f=s.actualBoundingBoxRight,h=Math.ceil(u),g=Math.ceil(c),m=Math.max(0,Math.min(o-t,Math.ceil(c)+Math.ceil(f))),p=Math.min(o-t,h+Math.ceil(d)),v=m+2*t,b=p+2*t,y=Math.max(v*b,0),T=new Uint8ClampedArray(y),x={data:T,width:v,height:b,glyphWidth:m,glyphHeight:p,glyphTop:h,glyphLeft:g,glyphAdvance:l};if(m===0||p===0)return x;var _=a.gridInner,R=a.gridOuter;i.clearRect(t,t,m,p),i.fillText(n,t+g,t+h);var E=i.getImageData(t,t,m,p);R.fill(Ct,0,y),_.fill(0,0,y);for(var L=0;L<p;L++)for(var D=0;D<m;D++){var F=E.data[4*(L*m+D)+3]/255;if(F!==0){var A=(L+t)*v+D+t;if(F===1)R[A]=0,_[A]=Ct;else{var I=.5-F;R[A]=I>0?I*I:0,_[A]=I<0?I*I:0}}}Nr(R,0,0,v,b,v,a.f,a.v,a.z),Nr(_,t,t,m,p,v,a.f,a.v,a.z);for(var w=0;w<y;w++){var k=Math.sqrt(R[w])-Math.sqrt(_[w]);T[w]=Math.round(255-255*(k/e+r))}return x}function Nr(a,n,t,e,r,i,o,s,l){for(var u=n;u<n+e;u++)Gr(a,t*i+u,i,r,o,s,l);for(var d=t;d<t+r;d++)Gr(a,d*i+n,1,e,o,s,l)}function Gr(a,n,t,e,r,i,o){i[0]=0,o[0]=-Ct,o[1]=Ct,r[0]=a[n];for(var s=1,l=0,u=0;s<e;s++){r[s]=a[n+s*t];var d=s*s;do{var c=i[l];u=(r[s]-r[c]+d-c*c)/(s-c)/2}while(u<=o[l]&&--l>-1);l++,i[l]=s,o[l]=u,o[l+1]=Ct}for(var f=0,h=0;f<e;f++){for(;o[h+1]<f;)h++;var g=i[h],m=f-g;a[n+f*t]=r[g]+m*m}}var Oe=function(a){function n(){var t,e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{};return Y(this,n),t=te(this,n),S(t,"fonts",new Map),S(t,"textures",[]),S(t,"cursor",{x:0,y:0,rowHeight:0,atlasIndex:0}),S(t,"pendingGlyphs",[]),S(t,"debounceTimer",null),t.options=B(B({},Se),e),t.canvas=document.createElement("canvas"),t.canvas.width=t.options.maxTextureSize,t.canvas.height=t.options.maxTextureSize,t.ctx=t.canvas.getContext("2d",{willReadFrequently:!0}),t.measureCanvas=document.createElement("canvas"),t.measureCtx=t.measureCanvas.getContext("2d"),t.textures.push(t.ctx.getImageData(0,0,1,1)),t}return ne(n,a),K(n,[{key:"getFontKey",value:function(e){return"".concat(e.family,"-").concat(e.weight,"-").concat(e.style)}},{key:"registerFont",value:function(e){var r=this.getFontKey(e);if(this.fonts.has(r))return r;var i=Fl(this.options.fontSize,e.family,e.weight,e.style,this.options.buffer);return this.fonts.set(r,{descriptor:e,generator:i,glyphs:new Map}),r}},{key:"ensureGlyphs",value:function(e,r){var i=this.fonts.get(r);if(!i)throw new Error('Font "'.concat(r,'" is not registered. Call registerFont() first.'));var o=!1,s=M(e),l;try{for(s.s();!(l=s.n()).done;){var u=l.value,d=u.codePointAt(0);d!==void 0&&(i.glyphs.has(d)||(this.pendingGlyphs.push({fontKey:r,charCode:d}),o=!0))}}catch(c){s.e(c)}finally{s.f()}o&&this.scheduleTextureGeneration()}},{key:"measureText",value:function(e,r){var i=this.fonts.get(r);if(!i)throw new Error('Font "'.concat(r,'" is not registered.'));var o=i.descriptor,s=o.family,l=o.weight,u=o.style;return this.measureCtx.font="".concat(u," ").concat(l," ").concat(this.options.fontSize,"px ").concat(s),this.measureCtx.measureText(e).width}},{key:"getGlyph",value:function(e,r){var i=this.fonts.get(r);if(i)return i.glyphs.get(e)}},{key:"getTextures",value:function(){return this.textures}},{key:"getFontCount",value:function(){return this.fonts.size}},{key:"getGlyphCount",value:function(){var e=0,r=M(this.fonts.values()),i;try{for(r.s();!(i=r.n()).done;){var o=i.value;e+=o.glyphs.size}}catch(s){r.e(s)}finally{r.f()}return e}},{key:"hasPendingGlyphs",value:function(){return this.pendingGlyphs.length>0}},{key:"flush",value:function(){this.debounceTimer&&(clearTimeout(this.debounceTimer),this.debounceTimer=null),this.generateTextures()}},{key:"destroy",value:function(){this.debounceTimer&&clearTimeout(this.debounceTimer),this.fonts.clear(),this.textures=[],this.pendingGlyphs=[],this.removeAllListeners()}},{key:"scheduleTextureGeneration",value:function(){var e=this;this.debounceTimer===null&&(this.options.debounceTimeout===null?this.generateTextures():this.debounceTimer=setTimeout(function(){e.debounceTimer=null,e.generateTextures()},this.options.debounceTimeout))}},{key:"generateTextures",value:function(){if(this.pendingGlyphs.length!==0){var e=this.options,r=e.maxTextureSize,i=e.buffer,o=e.radius,s=e.cutoff,l=M(this.pendingGlyphs),u;try{for(l.s();!(u=l.n()).done;){var d=u.value,c=d.fontKey,f=d.charCode,h=this.fonts.get(c);if(!(!h||h.glyphs.has(f))){var g=String.fromCodePoint(f),m=Il(h.generator,g,i,o,s),p=m.width,v=m.height;this.cursor.x+p+wt>r&&(this.cursor.x=0,this.cursor.y+=this.cursor.rowHeight+wt,this.cursor.rowHeight=0),this.cursor.y+v+wt>r&&(this.finalizeCurrentTexture(),this.cursor={x:0,y:0,rowHeight:0,atlasIndex:this.cursor.atlasIndex+1},this.ctx.clearRect(0,0,r,r));for(var b=m.data,y=new Uint8ClampedArray(p*v*4),T=0;T<b.length;T++){var x=T*4;y[x]=255,y[x+1]=255,y[x+2]=255,y[x+3]=b[T]}var _=new ImageData(y,p,v);this.ctx.putImageData(_,this.cursor.x,this.cursor.y);var R={charCode:f,width:m.glyphWidth,height:m.glyphHeight,bearingX:-m.glyphLeft-i,bearingY:m.glyphTop+i,advance:m.glyphAdvance,atlasX:this.cursor.x,atlasY:this.cursor.y,atlasWidth:p,atlasHeight:v,atlasIndex:this.cursor.atlasIndex};h.glyphs.set(f,R),this.cursor.x+=p+wt,this.cursor.rowHeight=Math.max(this.cursor.rowHeight,v)}}}catch(E){l.e(E)}finally{l.f()}this.finalizeCurrentTexture(),this.pendingGlyphs=[],this.emit(n.ATLAS_UPDATED_EVENT,{textures:this.textures,glyphCount:this.getGlyphCount()})}}},{key:"finalizeCurrentTexture",value:function(){var e=this.options.maxTextureSize,r=this.cursor.y>0||this.cursor.rowHeight>0,i=Math.min(e,Math.max(this.cursor.x,r?e:1)),o=Math.min(e,this.cursor.y+this.cursor.rowHeight+wt),s=this.ctx.getImageData(0,0,i,o);this.cursor.atlasIndex>=this.textures.length?this.textures.push(s):this.textures[this.cursor.atlasIndex]=s}}])}(Or.EventEmitter);S(Oe,"ATLAS_UPDATED_EVENT","atlasUpdated");var Nl=Se.fontSize;function Gl(){var a=`  // -------------------------------------------------------------------------
  // Step 3: Calculate position offset from the shared edge distance
  // -------------------------------------------------------------------------
  vec2 positionOffset = vec2(0.0);

  if (a_positionMode < 4.0) {
    vec2 screenDir = getLabelDirection(a_positionMode);
    float boundaryDistPixels = nodeRadiusPixels * edgeDist;
    positionOffset = screenDir * (boundaryDistPixels + margin);
  }`,n=`#version 300 es

// ============================================================================
// Attributes
// ============================================================================

// Per-character (instanced)
in float a_nodeIndex;        // Index into node data texture
in vec2 a_charOffset;        // Character offset from label origin (pixels)
in vec2 a_charSize;          // Character dimensions (pixels)
in vec4 a_texCoords;         // Atlas coords: (x, y, width, height) in pixels
in vec4 a_color;             // Text color (RGBA)
in float a_margin;           // Gap between node edge and label (pixels)
in float a_positionMode;     // Position: 0=right, 1=left, 2=above, 3=below, 4=over
in float a_labelWidth;       // Total label width (pixels)
in float a_labelHeight;      // Label height (pixels)
in float a_verticalCenter;   // Vertical center offset from baseline (pixels)
in float a_textHeight;       // Actual text height: maxAscent + maxDescent (pixels)
in float a_labelAngle;       // Label rotation angle (radians)

// Per-vertex (constant quad corners)
in vec2 a_quadCorner;        // Quad corner: [-1,-1], [1,-1], [-1,1], [1,1]

// ============================================================================
// Uniforms
// ============================================================================

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform vec2 u_atlasSize;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_nodeFrameTexture;
uniform int u_nodeFrameTextureWidth;
uniform float u_zoomLabelSizeRatio;
uniform float u_labelPixelSnapping;
uniform float u_pixelRatio;

// ============================================================================
// Varyings
// ============================================================================

out vec2 v_texCoord;
out vec4 v_color;
out float v_fontScale;

// ============================================================================
// Constants
// ============================================================================

const float bias = 255.0 / 254.0;
const float ATLAS_FONT_SIZE = `.concat(ae(Nl),`;

// ============================================================================
// Helper Functions
// ============================================================================

`).concat(Le,`
`).concat(Ue,`
`).concat(ct,`
`).concat(jr,`

// ============================================================================
// Main
// ============================================================================

void main() {
  // -------------------------------------------------------------------------
  // Step 0: Fetch node data + shared edge distance from textures
  // -------------------------------------------------------------------------
  // Node-data texture format: vec4(x, y, size, shapeId)
  // 2D texture layout: texCoord = (index % width, index / width)
  int nodeIdx = int(a_nodeIndex);
  vec4 nodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  vec2 a_anchorPosition = nodeData.xy;
  float a_nodeSize = nodeData.z;

  // Normalized edge distance from the shared frame texture (the frame-pass ran
  // the SDF search once; the label just reads the result).
  float edgeDist = readFrameTexel(u_nodeFrameTexture, u_nodeFrameTextureWidth, nodeIdx).r;

  // Per-node label rotation alignment: 0 = viewport, 1 = label turns with camera.
  float labelRotation = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).g;

  // Apply zoom-dependent label size scaling
  // Positional values are in CSS pixels; multiply by u_pixelRatio to convert to
  // physical pixels, which is what the NDC conversion (/ u_resolution) expects.
  float zoomScale = u_zoomLabelSizeRatio;
  float margin = a_margin * zoomScale * u_pixelRatio;
  vec2 charOffset = a_charOffset * zoomScale * u_pixelRatio;
  vec2 charSize = a_charSize * zoomScale * u_pixelRatio;
  float labelWidth = a_labelWidth * zoomScale * u_pixelRatio;
  float labelHeight = a_labelHeight * zoomScale;

  // Font scale: ratio of CSS label size to the base atlas font size.
  // Divided by u_pixelRatio because the atlas is generated at ATLAS_FONT_SIZE * pixelRatio,
  // which cancels out the u_pixelRatio in the fragment shader's gamma formula and keeps
  // the anti-aliasing band width consistent across pixel densities.
  v_fontScale = a_labelHeight * zoomScale / (ATLAS_FONT_SIZE * u_pixelRatio);

  // -------------------------------------------------------------------------
  // Step 1: Transform node position to clip space
  // -------------------------------------------------------------------------
  vec3 anchorClip = u_matrix * vec3(a_anchorPosition, 1.0);

  // -------------------------------------------------------------------------
  // Step 2: Convert node size to screen pixels
  // -------------------------------------------------------------------------
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float nodeRadiusGraphSpace = a_nodeSize * u_correctionRatio / u_sizeRatio * 2.0;
  float nodeRadiusNDC = nodeRadiusGraphSpace * matrixScaleX;
  float nodeRadiusPixels = nodeRadiusNDC * u_resolution.x / 2.0;

`).concat(a,`

  // -------------------------------------------------------------------------
  // Step 4: Calculate final vertex position
  // -------------------------------------------------------------------------
  vec2 cornerOffset = (a_quadCorner + 1.0) * 0.5;
  vec2 charPixelPos = positionOffset + charOffset + cornerOffset * charSize;

  // Apply text alignment based on position mode
  float verticalCenter = a_verticalCenter * zoomScale * u_pixelRatio;
  float textHeight = a_textHeight * zoomScale * u_pixelRatio;
  float baselineToDescent = textHeight / 2.0 - verticalCenter;
  float baselineToAscent = textHeight / 2.0 + verticalCenter;

  if (a_positionMode < 0.5) {
    // Right: vertically center
    charPixelPos.y += verticalCenter;
  } else if (a_positionMode < 1.5) {
    // Left: right-align and vertically center
    charPixelPos.x -= labelWidth;
    charPixelPos.y += verticalCenter;
  } else if (a_positionMode < 2.5) {
    // Above: center horizontally, bottom of text at anchor
    charPixelPos.x -= labelWidth * 0.5;
    charPixelPos.y -= baselineToDescent;
  } else if (a_positionMode < 3.5) {
    // Below: center horizontally, top of text at anchor
    charPixelPos.x -= labelWidth * 0.5;
    charPixelPos.y += baselineToAscent;
  } else {
    // Over: center both
    charPixelPos.x -= labelWidth * 0.5;
    charPixelPos.y += verticalCenter;
  }

  // Apply label angle rotation. Graph-aligned labels add the camera angle so the
  // whole label orbits the node in lockstep with the frame-pass edge distance.
  float labelAngle = a_labelAngle - labelRotation * u_cameraAngle;
  float la_c = cos(labelAngle);
  float la_s = sin(labelAngle);
  mat2 labelRotMat = mat2(la_c, -la_s, la_s, la_c);
  charPixelPos = labelRotMat * charPixelPos;

  // Snap node center to pixel grid so label/backdrop/attachment move as a unit
  vec2 nodeScreen = vec2(
    (anchorClip.x + 1.0) * u_resolution.x,
    (1.0 - anchorClip.y) * u_resolution.y
  ) * 0.5;
  charPixelPos += (round(nodeScreen) - nodeScreen) * u_labelPixelSnapping;

  // Convert to NDC (flip Y: screen Y-down -> clip Y-up)
  vec2 ndcOffset = vec2(charPixelPos.x, -charPixelPos.y) * 2.0 / u_resolution;
  gl_Position = vec4(anchorClip.xy + ndcOffset, 0.0, 1.0);

  // -------------------------------------------------------------------------
  // Step 5: Texture coordinates
  // -------------------------------------------------------------------------
  v_texCoord = (a_texCoords.xy + cornerOffset * a_texCoords.zw) / u_atlasSize;

  // -------------------------------------------------------------------------
  // Step 6: Pass color
  // -------------------------------------------------------------------------
  v_color = a_color;
  v_color.a *= bias;
}
`);return n}function zl(){var a=`#version 300 es
precision highp float;

in vec2 v_texCoord;
in vec4 v_color;
in float v_fontScale;

uniform sampler2D u_atlas;
uniform float u_gamma;
uniform float u_sdfBuffer;
uniform float u_pixelRatio;

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

void main() {
  #ifdef PICKING_MODE
    // Labels are not pickable - discard all fragments in picking mode
    fragColor = vec4(0.0);
    discard;
  #else
    // Sample SDF value from atlas (high = inside glyph, low = outside)
    float sdfValue = texture(u_atlas, v_texCoord).a;

    // Edge threshold: 1.0 - cutoff = 0.75 for default cutoff=0.25
    // This is where the glyph edge is located in the SDF
    float edgeThreshold = 1.0 - u_sdfBuffer;

    // Gamma controls the anti-aliasing band width.
    // Scale inversely with font scale so small labels get a wider AA band
    // (smoother) and large labels get a tighter band (sharper).
    float gamma = u_gamma / (u_pixelRatio * v_fontScale);

    // Pure gamma-based anti-aliasing using smoothstep
    // The AA band extends from (threshold - gamma) to (threshold + gamma)
    float alpha = smoothstep(edgeThreshold - gamma, edgeThreshold + gamma, sdfValue);

    // Premultiplied alpha output for correct blending
    float finalAlpha = v_color.a * alpha;
    fragColor = vec4(v_color.rgb * finalAlpha, finalAlpha);
  #endif
}
`;return a}function Ml(){return["u_matrix","u_sizeRatio","u_correctionRatio","u_cameraAngle","u_resolution","u_atlasSize","u_atlas","u_gamma","u_sdfBuffer","u_pixelRatio","u_nodeDataTexture","u_nodeDataTextureWidth","u_nodeFrameTexture","u_nodeFrameTextureWidth","u_zoomLabelSizeRatio","u_labelPixelSnapping"]}function Bl(){return{vertexShader:Gl(),fragmentShader:zl(),uniforms:Ml()}}function Wl(a,n,t,e){var r,i,o=e.label,s=o===void 0?{}:o,l=(r=s.margin)!==null&&r!==void 0?r:dt,u=(i=s.zoomToLabelSizeRatioFunction)!==null&&i!==void 0?i:function(){return 1},d=Bl(),c=function(f){function h(g,m,p){var v,b,y,T;if(Y(this,h),T=te(this,h,[g,m,p]),S(T,"atlasTexture",null),S(T,"atlasNeedsUpdate",!1),S(T,"labelGlyphCache",new Map),T.atlasFontSize=Se.fontSize*Dt(),T.atlasManager=new Oe({fontSize:T.atlasFontSize}),T.gamma=.025,T.sdfBuffer=Se.cutoff,T.atlasTexture=g.createTexture(),!T.atlasTexture)throw new Error("NodeLabelProgram: failed to create atlas texture");g.bindTexture(g.TEXTURE_2D,T.atlasTexture),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR),g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR),g.bindTexture(g.TEXTURE_2D,null),T.atlasManager.on(Oe.ATLAS_UPDATED_EVENT,function(){T.atlasNeedsUpdate=!0});var x={family:((v=s.font)===null||v===void 0?void 0:v.family)||"sans-serif",weight:((b=s.font)===null||b===void 0?void 0:b.weight)||"normal",style:((y=s.font)===null||y===void 0?void 0:y.style)||"normal"};return T.defaultFontKey=T.atlasManager.registerFont(x),T}return ne(h,f),K(h,[{key:"getDefinition",value:function(){var m=WebGL2RenderingContext,p=m.FLOAT,v=m.UNSIGNED_BYTE,b=m.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:d.vertexShader,FRAGMENT_SHADER_SOURCE:d.fragmentShader,METHOD:b,UNIFORMS:d.uniforms,ATTRIBUTES:[{name:"a_nodeIndex",size:1,type:p},{name:"a_charOffset",size:2,type:p},{name:"a_charSize",size:2,type:p},{name:"a_texCoords",size:4,type:p},{name:"a_color",size:4,type:v,normalized:!0},{name:"a_margin",size:1,type:p},{name:"a_positionMode",size:1,type:p},{name:"a_labelWidth",size:1,type:p},{name:"a_labelHeight",size:1,type:p},{name:"a_verticalCenter",size:1,type:p},{name:"a_textHeight",size:1,type:p},{name:"a_labelAngle",size:1,type:p}],CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:p}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"prepareLabelGlyphs",value:function(m,p){if(p.hidden||!p.text){this.labelGlyphCache.delete(m);return}var v=p.text,b=p.fontKey||this.defaultFontKey;this.atlasManager.ensureGlyphs(v,b);var y=[],T=[],x=0,_=0,R=0,E=M(v),L;try{for(E.s();!(L=E.n()).done;){var D=L.value,F=D.codePointAt(0);if(F===void 0){y.push(void 0),T.push(x);continue}var A=this.atlasManager.getGlyph(F,b);y.push(A),T.push(x),A&&(x+=A.advance,_=Math.max(_,A.bearingY),R=Math.max(R,A.atlasHeight-A.bearingY))}}catch(I){E.e(I)}finally{E.f()}this.labelGlyphCache.set(m,{glyphs:y,xOffsets:T,totalWidth:x,totalHeight:_+R,verticalCenterOffset:(_-R)/2})}},{key:"processCharacter",value:function(m,p,v,b){var y=this.floats,T=this.STRIDE,x=m*T,_=this.labelGlyphCache.get(p.parentKey);if(!_||!_.glyphs[b]){for(var R=0;R<T;R++)y[x+R]=0;return}var E=_.glyphs[b],L=_.xOffsets[b],D=p.size/this.atlasFontSize,F=ve(p.color),A=x;y[A++]=p.nodeIndex,y[A++]=(L+E.bearingX)*D,y[A++]=-E.bearingY*D,y[A++]=E.atlasWidth*D,y[A++]=E.atlasHeight*D,y[A++]=E.atlasX,y[A++]=E.atlasY,y[A++]=E.atlasWidth,y[A++]=E.atlasHeight,y[A++]=F,y[A++]=p.margin,y[A++]=ut[p.position],y[A++]=_.totalWidth*D,y[A++]=p.size,y[A++]=_.verticalCenterOffset*D,y[A++]=_.totalHeight*D,y[A++]=p.labelAngle}},{key:"processLabel",value:function(m,p,v){return this.prepareLabelGlyphs(m,v),ie(h,"processLabel",this,3)([m,p,v])}},{key:"updateAtlasTexture",value:function(){if(this.atlasNeedsUpdate){var m=this.normalProgram.gl,p=this.atlasManager.getTextures();if(p.length!==0){var v=p[0];m.bindTexture(m.TEXTURE_2D,this.atlasTexture),m.texImage2D(m.TEXTURE_2D,0,m.RGBA,v.width,v.height,0,m.RGBA,m.UNSIGNED_BYTE,v.data),m.bindTexture(m.TEXTURE_2D,null),this.atlasNeedsUpdate=!1}}}},{key:"setUniforms",value:function(m,p){var v=p.gl,b=p.uniformLocations;v.uniformMatrix3fv(b.u_matrix,!1,m.matrix),v.uniform1f(b.u_sizeRatio,m.sizeRatio),v.uniform1f(b.u_correctionRatio,m.correctionRatio),v.uniform1f(b.u_cameraAngle,m.cameraAngle),v.uniform2f(b.u_resolution,m.width*m.pixelRatio,m.height*m.pixelRatio);var y=this.atlasManager.getTextures();y.length>0?v.uniform2f(b.u_atlasSize,y[0].width,y[0].height):v.uniform2f(b.u_atlasSize,1,1),v.activeTexture(v.TEXTURE0),v.bindTexture(v.TEXTURE_2D,this.atlasTexture),v.uniform1i(b.u_atlas,0),b.u_nodeDataTexture!==void 0&&v.uniform1i(b.u_nodeDataTexture,m.nodeDataTextureUnit),b.u_nodeDataTextureWidth!==void 0&&v.uniform1i(b.u_nodeDataTextureWidth,m.nodeDataTextureWidth),v.uniform1i(b.u_nodeFrameTexture,m.nodeFrameTextureUnit),v.uniform1i(b.u_nodeFrameTextureWidth,m.nodeFrameTextureWidth),v.uniform1f(b.u_gamma,this.gamma),v.uniform1f(b.u_sdfBuffer,this.sdfBuffer),v.uniform1f(b.u_pixelRatio,m.pixelRatio),v.uniform1f(b.u_zoomLabelSizeRatio,1/h.zoomToLabelSizeRatioFunction(m.zoomRatio)),v.uniform1f(b.u_labelPixelSnapping,m.labelPixelSnapping)}},{key:"renderProgram",value:function(m,p){this.updateAtlasTexture(),this.atlasManager.hasPendingGlyphs()&&(this.atlasManager.flush(),this.updateAtlasTexture()),ie(h,"renderProgram",this,3)([m,p])}},{key:"registerFont",value:function(m){var p=arguments.length>1&&arguments[1]!==void 0?arguments[1]:"normal",v=arguments.length>2&&arguments[2]!==void 0?arguments[2]:"normal";return this.atlasManager.registerFont({family:m,weight:p,style:v})}},{key:"getAtlasManager",value:function(){return this.atlasManager}},{key:"measureLabel",value:function(m,p,v){var b=v||this.defaultFontKey;this.atlasManager.ensureGlyphs(m,b),this.atlasManager.hasPendingGlyphs()&&this.atlasManager.flush();var y=0,T=0,x=0,_=M(m),R;try{for(_.s();!(R=_.n()).done;){var E=R.value,L=E.codePointAt(0);if(L!==void 0){var D=this.atlasManager.getGlyph(L,b);D&&(y+=D.advance,T=Math.max(T,D.bearingY),x=Math.max(x,D.atlasHeight-D.bearingY))}}}catch(A){_.e(A)}finally{_.f()}var F=p/this.atlasFontSize;return{width:y*F,height:p,textHeight:(T+x)*F}}},{key:"ensureGlyphsReady",value:function(m,p){var v=p||this.defaultFontKey,b=M(m),y;try{for(b.s();!(y=b.n()).done;){var T=y.value;this.atlasManager.ensureGlyphs(T,v)}}catch(x){b.e(x)}finally{b.f()}this.atlasManager.flush()}},{key:"kill",value:function(){var m=this.normalProgram.gl;this.atlasTexture&&(m.deleteTexture(this.atlasTexture),this.atlasTexture=null),this.atlasManager.destroy(),this.labelGlyphCache.clear(),ie(h,"kill",this,3)([])}}])}(Qr);return S(c,"labelMargin",l),S(c,"zoomToLabelSizeRatioFunction",u),new c(a,n,t)}var Ol=`#version 300 es
precision highp float;

in float v_edgeDist;

// R32F target: only the .r channel is stored.
out vec4 fragColor;

void main() {
  fragColor = vec4(v_edgeDist, 0.0, 0.0, 0.0);
}
`;function Ul(a,n,t){var e=ca(a),r=Ft(a).map(function(g){return"uniform ".concat(g.type," ").concat(g.name,";")}).join(`
`),i=fl(a,t),o=i.code,s=i.multiShape,l=ht(a,n),u=Object.keys(l.specs).map(function(g){return"float v_".concat(g,";")}).join(`
`),d=lt(l,{varPrefix:"nodeAttr",baseTexelExpr:"nodeIdx * u_layerAttributeTexelsPerNode",textureWidthUniform:"u_layerAttributeTextureWidth",textureSamplerUniform:"u_layerAttributeTexture"}),c=d.fetchCode,f=d.varyingAssignments,h=`#version 300 es
precision highp float;

uniform float u_cameraAngle;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform float u_frameTextureWidth;
uniform float u_frameTextureHeight;
uniform sampler2D u_layerAttributeTexture;
uniform int u_layerAttributeTextureWidth;
uniform int u_layerAttributeTexelsPerNode;
`.concat(r,`

in float a_nodeIndex;     // node-data texture index (also the target frame texel)
in float a_positionMode;  // 0=right 1=left 2=above 3=below 4=over
in float a_labelAngle;    // intrinsic label angle (radians)

out float v_edgeDist;

// Shape attributes (plain globals: this pass is vertex-only)
`).concat(u,`

`).concat(Le,`
`).concat(Ue,`
`).concat(e,`
`).concat(o,`
`).concat(jr,`

void main() {
  int nodeIdx = int(a_nodeIndex);
`).concat(c,`
`).concat(f,`
  `).concat(s?`// Multi-shape: the shape id lives in the node-data texture's .w channel:
  g_shapeId = int(readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx).w);`:"// Single-shape mode, shape id not needed",`

  // Per-node rotation alignment (0 = viewport, 1 = graph).
  vec4 nodeFlags = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, nodeIdx);
  float nodeRotation = nodeFlags.r;
  float labelRotation = nodeFlags.g;

  // Effective angle: intrinsic (style-given) plus the camera angle when the label
  // is graph-aligned. The companions place the box at this same angle.
  float effectiveAngle = a_labelAngle - labelRotation * u_cameraAngle;

  // The "over" mode (4) sits on the node center, so it has no edge distance.
  float edgeDist = 0.0;
  if (a_positionMode < 4.0) {
    vec2 screenDir = getLabelDirection(a_positionMode);
    // Rotate by the effective label angle. Inlined rather than via rotate2D()
    // because the shape SDFs (getShapeGLSLForShapes) already define that helper
    // for multi-shape programs, and redefining it would be a GLSL error.
    float ea_c = cos(effectiveAngle);
    float ea_s = sin(effectiveAngle);
    vec2 rotatedScreenDir = mat2(ea_c, -ea_s, ea_s, ea_c) * screenDir;
    // Screen (Y-down) -> SDF (Y-up).
    vec2 sdfDir = vec2(rotatedScreenDir.x, -rotatedScreenDir.y);
    // Counter-rotate into the shape's local frame for graph-aligned nodes, so the
    // boundary is queried against the shape's actual on-screen orientation.
    float nodeCa = -u_cameraAngle * nodeRotation;
    float nc = cos(nodeCa), ns = sin(nodeCa);
    sdfDir = mat2(nc, -ns, ns, nc) * sdfDir;
    edgeDist = findEdgeDistance(sdfDir, 1.0);
  }
  v_edgeDist = edgeDist;

  // Scatter to this node's texel center in the frame texture.
  float x = mod(a_nodeIndex, u_frameTextureWidth);
  float y = floor(a_nodeIndex / u_frameTextureWidth);
  vec2 ndc = (vec2(x, y) + 0.5) / vec2(u_frameTextureWidth, u_frameTextureHeight) * 2.0 - 1.0;
  gl_Position = vec4(ndc, 0.0, 1.0);
  gl_PointSize = 1.0;
}
`);return h}var Jr=function(){function a(n,t){Y(this,a),S(this,"uniformLocations",{});var e=t.shapes,r=t.layers,i=t.shapeGlobalIds;if(e.length===0)throw new Error("NodeLabelFramePass: at least one shape must be provided");this.gl=n,this.shapeUniforms=Ft(e),this.hasAttributeData=Object.keys(ht(e,r).offsets).length>0,this.vertexShader=la(n,Ul(e,r,i)),this.fragmentShader=ua(n,Ol),this.program=da(n,[this.vertexShader,this.fragmentShader]);var o=["u_cameraAngle","u_nodeDataTexture","u_nodeDataTextureWidth","u_frameTextureWidth","u_frameTextureHeight","u_layerAttributeTexture","u_layerAttributeTextureWidth","u_layerAttributeTexelsPerNode"].concat($(this.shapeUniforms.map(function(v){return v.name}))),s=M(o),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;this.uniformLocations[u]=n.getUniformLocation(this.program,u)}}catch(v){s.e(v)}finally{s.f()}var d=a.FLOATS_PER_POINT*4;this.vao=n.createVertexArray(),this.buffer=n.createBuffer(),n.bindVertexArray(this.vao),n.bindBuffer(n.ARRAY_BUFFER,this.buffer);var c=M([["a_nodeIndex",0],["a_positionMode",4],["a_labelAngle",8]]),f;try{for(c.s();!(f=c.n()).done;){var h=Q(f.value,2),g=h[0],m=h[1],p=n.getAttribLocation(this.program,g);p>=0&&(n.enableVertexAttribArray(p),n.vertexAttribPointer(p,1,n.FLOAT,!1,d,m))}}catch(v){c.e(v)}finally{c.f()}n.bindVertexArray(null)}return K(a,[{key:"run",value:function(t,e,r,i,o){if(e!==0){var s=this.gl;s.useProgram(this.program),s.bindVertexArray(this.vao),s.bindBuffer(s.ARRAY_BUFFER,this.buffer),s.bufferData(s.ARRAY_BUFFER,t.subarray(0,e*a.FLOATS_PER_POINT),s.DYNAMIC_DRAW);var l=this.uniformLocations;s.uniform1f(l.u_cameraAngle,i.cameraAngle),s.uniform1i(l.u_nodeDataTexture,i.nodeDataTextureUnit),s.uniform1i(l.u_nodeDataTextureWidth,i.nodeDataTextureWidth),s.uniform1f(l.u_frameTextureWidth,r.getTextureWidth()),s.uniform1f(l.u_frameTextureHeight,r.getTextureHeight()),this.hasAttributeData&&o&&(o.bind(Ie),l.u_layerAttributeTexture&&s.uniform1i(l.u_layerAttributeTexture,Ie),l.u_layerAttributeTextureWidth&&s.uniform1i(l.u_layerAttributeTextureWidth,o.getTextureWidth()),l.u_layerAttributeTexelsPerNode&&s.uniform1i(l.u_layerAttributeTexelsPerNode,o.getTexelsPerItem()));var u=M(this.shapeUniforms),d;try{for(u.s();!(d=u.n()).done;){var c=d.value;ga(s,this.uniformLocations[c.name],c)}}catch(f){u.e(f)}finally{u.f()}r.bindAsRenderTarget(),s.disable(s.BLEND),s.disable(s.DEPTH_TEST),s.drawArrays(s.POINTS,0,e),s.bindFramebuffer(s.FRAMEBUFFER,null),s.bindVertexArray(null)}}},{key:"kill",value:function(){var t=this.gl;t.deleteProgram(this.program),t.deleteShader(this.vertexShader),t.deleteShader(this.fragmentShader),t.deleteBuffer(this.buffer),t.deleteVertexArray(this.vao)}}])}();S(Jr,"FLOATS_PER_POINT",3);function ei(a,n,t,e,r){var i,o=e.label,s=o===void 0?{}:o,l=e.shapes;if(l.length===0)throw new Error("createNodeProgram: at least one shape must be provided in 'shapes'");var u={},d=[],c;l.forEach(function(R,E){var L=al(R);E===0&&(c=L),u[R.name]=E,d[E]=kt(L)});var f=$(e.layers),h=Ir({shapes:l,layers:f,shapeGlobalIds:l.length>1?d:void 0,antialias:r}),g=Wl(a,null,t,{label:s}),m=Ll(a,null,t,{shapes:l,layers:f,getAttributeTexture:function(){return _.getAttributeTexture()},label:s,shapeGlobalIds:l.length>1?d:void 0}),p=kl(a,n,t,{label:s}),v=e.labelAttachments&&Object.keys(e.labelAttachments).length>0?xl(a,null,t,{label:s}):null,b=new Jr(a,{shapes:l,layers:f,shapeGlobalIds:l.length>1?d:void 0}),y=An(l,f),T=me(y),x=(i=function(R){function E(L,D,F){var A;Y(this,E),A=te(this,E,[L,D,F]),S(A,"layerLifecycles",new Map),S(A,"layersNeedingRegeneration",new Set),S(A,"attrDescriptors",[]),A._pickingBuffer=D;var I=x.layerTextures.get(L);I||(I=new Sn(L,T),x.layerTextures.set(L,I)),A.layerAttributeTexture=I;var w=x.textureRefCounts.get(L)||0;x.textureRefCounts.set(L,w+1),A.packedAttributeData=new Float32Array(T.floatsPerItem),f.forEach(function(G,N){if(G.lifecycle){var P={gl:L,renderer:{refresh:function(){return F.refresh()}},getUniformLocation:function(H){return L.getUniformLocation(A.normalProgram.program,H)},requestShaderRegeneration:function(){A.layersNeedingRegeneration.add(N)},requestRefresh:function(){F.refresh()}},C=G.lifecycle(P);A.layerLifecycles.set(N,C)}}),A.layerLifecycles.forEach(function(G){var N;(N=G.init)===null||N===void 0||N.call(G)});var k=new Map;return A.layerLifecycles.forEach(function(G,N){G.getAttributeData&&k.set(N,G)}),A.attrDescriptors=En(y,T,k),A}return ne(E,R),K(E,[{key:"getDefinition",value:function(){var D=WebGL2RenderingContext,F=D.FLOAT,A=D.TRIANGLE_STRIP;return{VERTICES:4,VERTEX_SHADER_SOURCE:h.vertexShader,FRAGMENT_SHADER_SOURCE:h.fragmentShader,METHOD:A,UNIFORMS:h.uniforms,ATTRIBUTES:h.attributes,CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:F}],CONSTANT_DATA:[[-1,-1],[1,-1],[-1,1],[1,1]]}}},{key:"maybeRegenerateShaders",value:function(){var D=this;if(this.layersNeedingRegeneration.size!==0){f=f.map(function(N,P){if(D.layersNeedingRegeneration.has(P)){var C=D.layerLifecycles.get(P);if(C!=null&&C.regenerate){var z=C.regenerate();return B(B({},z),{},{lifecycle:N.lifecycle})}}return N}),this.layersNeedingRegeneration.clear(),h=Ir({shapes:l,layers:f,shapeGlobalIds:l.length>1?d:void 0,antialias:this.renderer.getSetting("antialiasNodes")});var F=this.normalProgram.gl,A=this.normalProgram,I=A.program,w=A.buffer,k=A.vertexShader,G=A.fragmentShader;F.deleteProgram(I),F.deleteBuffer(w),F.deleteShader(k),F.deleteShader(G),this.normalProgram=this.getProgramInfo("normal",F,h.vertexShader,h.fragmentShader,this._pickingBuffer)}}},{key:"getAttributeTexture",value:function(){return this.layerAttributeTexture}},{key:"uploadLayerTexture",value:function(){this.layerAttributeTexture.upload()}},{key:"process",value:function(D,F,A,I){var w=F*this.STRIDE;if(A.visibility==="hidden"){for(var k=w+this.STRIDE;w<k;w++)this.floats[w]=0;this.floats[F*this.STRIDE]=Yr;return}this.processVisibleItem(at(D),w,A,I)}},{key:"processVisibleItem",value:function(D,F,A,I){var w,k=this.floats,G=this.ints;if(k[F++]=I,G[F++]=D,k[F++]=(w=A.opacity)!==null&&w!==void 0?w:1,T.floatsPerItem!==0){var N=this.packedAttributeData;Rn(this.attrDescriptors,A,N,A.color,this.layerLifecycles,0),this.layerAttributeTexture.updateAllAttributesAtRow(I,N)}}},{key:"setUniforms",value:function(D,F){var A=this,I=F.gl,w=F.uniformLocations;w.u_matrix&&I.uniformMatrix3fv(w.u_matrix,!1,D.matrix),w.u_sizeRatio&&I.uniform1f(w.u_sizeRatio,D.sizeRatio),w.u_correctionRatio&&I.uniform1f(w.u_correctionRatio,D.correctionRatio),w.u_pickingPadding&&I.uniform1f(w.u_pickingPadding,D.nodePickingPadding),w.u_cameraAngle&&I.uniform1f(w.u_cameraAngle,D.cameraAngle),w.u_nodeDataTexture&&I.uniform1i(w.u_nodeDataTexture,D.nodeDataTextureUnit),w.u_nodeDataTextureWidth&&I.uniform1i(w.u_nodeDataTextureWidth,D.nodeDataTextureWidth),w.u_layerAttributeTexture&&(this.layerAttributeTexture.bind(Ie),I.uniform1i(w.u_layerAttributeTexture,Ie)),w.u_layerAttributeTextureWidth&&I.uniform1i(w.u_layerAttributeTextureWidth,this.layerAttributeTexture.getTextureWidth()),w.u_layerAttributeTexelsPerNode&&I.uniform1i(w.u_layerAttributeTexelsPerNode,this.layerAttributeTexture.getTexelsPerItem()),l.forEach(function(k){k.uniforms.forEach(function(G){A.setTypedUniform(G,F)})}),f.forEach(function(k){k.uniforms.forEach(function(G){A.setTypedUniform(G,F)})})}},{key:"render",value:function(D,F,A){this.maybeRegenerateShaders(),ie(E,"render",this,3)([D,F,A])}},{key:"renderProgram",value:function(D,F){var A=F.gl,I=F.program;A.useProgram(I),F===this.normalProgram&&this.layerLifecycles.forEach(function(w){var k;(k=w.beforeRender)===null||k===void 0||k.call(w)}),ie(E,"renderProgram",this,3)([D,F])}},{key:"kill",value:function(){this.layerLifecycles.forEach(function(A){var I;(I=A.kill)===null||I===void 0||I.call(A)}),this.layerLifecycles.clear();var D=this.normalProgram.gl,F=(x.textureRefCounts.get(D)||1)-1;F<=0?(this.layerAttributeTexture.kill(),x.layerTextures.delete(D),x.textureRefCounts.delete(D)):x.textureRefCounts.set(D,F),ie(E,"kill",this,3)([])}}])}(He),S(i,"layerTextures",new WeakMap),S(i,"textureRefCounts",new WeakMap),i),_=new x(a,null,t);return{nodeProgram:_,labelProgram:g,backdropProgram:m,labelBackgroundProgram:p,attachmentProgram:v,framePass:b,shapeSlug:c,shapeNameToIndex:l.length>1?u:void 0,shapeGlobalIds:l.length>1?d:void 0}}var Ne=6;function Nt(a){var n=a.offsets,t=a.specs,e=a.floatsPerItem,r=Object.keys(n);if(r.length===0||e===0)return{uniformDeclarations:"",uniformNames:[],vertexVaryingDeclarations:"",fragmentVaryingDeclarations:"",fetchCode:"",varyingAssignments:""};var i=`
uniform sampler2D u_edgeAttributeTexture;
uniform int u_edgeAttributeTextureWidth;
uniform int u_edgeAttributeTexelsPerEdge;`,o=["u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"],s=r.map(function(h){var g=t[h].size===1?"float":"vec".concat(t[h].size);return"".concat(g," v_").concat(h,";")}),l=s.map(function(h){return"out ".concat(h)}).join(`
`),u=s.map(function(h){return"in ".concat(h)}).join(`
`),d=lt(a,{varPrefix:"attr",baseTexelExpr:"edgeIdx * u_edgeAttributeTexelsPerEdge",textureWidthUniform:"u_edgeAttributeTextureWidth",textureSamplerUniform:"u_edgeAttributeTexture"}),c=d.fetchCode,f=d.varyingAssignments;return{uniformDeclarations:i,uniformNames:o,vertexVaryingDeclarations:l,fragmentVaryingDeclarations:u,fetchCode:c,varyingAssignments:f}}function Hl(a){return`
float findSourceClampT_`.concat(a,`(vec2 source, float sourceSize, int sourceShapeId, float sourceRotateAlign, vec2 target, float margin) {
  float lo = 0.0, hi = 0.5;
  float nodeExtent = sourceSize * u_correctionRatio / u_sizeRatio * 2.0;
  float effectiveSize = 1.0 - u_correctionRatio / nodeExtent;

  // Counter-rotate the query point so viewport-aligned nodes (rotateAlign=0) are
  // clamped against their on-screen orientation; graph-aligned nodes skip it.
  float ca = u_cameraAngle * (1.0 - sourceRotateAlign);
  float rc = cos(ca), rs = sin(ca);
  mat2 rot = mat2(rc, -rs, rs, rc);

  for (int i = 0; i < 12; i++) {
    float mid = (lo + hi) * 0.5;
    vec2 pos = path_`).concat(a,`_position(mid, source, target);
    vec2 localPos = rot * ((pos - source) / nodeExtent);
    float sdf = querySDF(sourceShapeId, localPos, effectiveSize);
    if (sdf < 0.0) lo = mid;
    else hi = mid;
  }

  float pathLen = path_`).concat(a,`_length(source, target);
  float marginT = (margin * u_correctionRatio / u_sizeRatio) / pathLen;
  return (lo + hi) * 0.5 + marginT;
}
`)}function $l(a){return`
float findTargetClampT_`.concat(a,`(vec2 source, vec2 target, float targetSize, int targetShapeId, float targetRotateAlign, float margin) {
  float lo = 0.5, hi = 1.0;
  float nodeExtent = targetSize * u_correctionRatio / u_sizeRatio * 2.0;
  float effectiveSize = 1.0 - u_correctionRatio / nodeExtent;

  // See findSourceClampT_ for the rotation rationale.
  float ca = u_cameraAngle * (1.0 - targetRotateAlign);
  float rc = cos(ca), rs = sin(ca);
  mat2 rot = mat2(rc, -rs, rs, rc);

  for (int i = 0; i < 12; i++) {
    float mid = (lo + hi) * 0.5;
    vec2 pos = path_`).concat(a,`_position(mid, source, target);
    vec2 localPos = rot * ((pos - target) / nodeExtent);
    float sdf = querySDF(targetShapeId, localPos, effectiveSize);
    if (sdf < 0.0) hi = mid;
    else lo = mid;
  }

  float pathLen = path_`).concat(a,`_length(source, target);
  float marginT = (margin * u_correctionRatio / u_sizeRatio) / pathLen;
  return (lo + hi) * 0.5 - marginT;
}
`)}function ti(a){return`
// Auto-generated numerical tangent (from position via finite differences)
vec2 path_`.concat(a,`_tangent(float t, vec2 source, vec2 target) {
  float epsilon = 0.001;
  float t1 = max(0.0, t - epsilon);
  float t2 = min(1.0, t + epsilon);
  vec2 p1 = path_`).concat(a,`_position(t1, source, target);
  vec2 p2 = path_`).concat(a,`_position(t2, source, target);
  return normalize(p2 - p1);
}

// Auto-generated normal (perpendicular to tangent)
vec2 path_`).concat(a,`_normal(float t, vec2 source, vec2 target) {
  vec2 tangent = path_`).concat(a,`_tangent(t, source, target);
  return vec2(-tangent.y, tangent.x);
}
`)}function Vl(a){return`
// Auto-generated path length (samples position 16 times)
float path_`.concat(a,`_length(vec2 source, vec2 target) {
  float len = 0.0;
  vec2 prev = path_`).concat(a,`_position(0.0, source, target);
  for (int i = 1; i <= 16; i++) {
    float t = float(i) / 16.0;
    vec2 curr = path_`).concat(a,`_position(t, source, target);
    len += length(curr - prev);
    prev = curr;
  }
  return len;
}
`)}function Xl(a){return`
// Auto-generated closest_t (coarse sample + ternary search)
float path_`.concat(a,`_closest_t(vec2 p, vec2 source, vec2 target) {
  // Coarse search: find best among 10 samples
  float bestT = 0.0;
  float bestDist = 1e10;
  for (int i = 0; i <= 10; i++) {
    float t = float(i) / 10.0;
    vec2 pos = path_`).concat(a,`_position(t, source, target);
    float d = length(p - pos);
    if (d < bestDist) {
      bestDist = d;
      bestT = t;
    }
  }

  // Refine with ternary search
  float lo = max(0.0, bestT - 0.1);
  float hi = min(1.0, bestT + 0.1);
  for (int i = 0; i < 10; i++) {
    float mid1 = lo + (hi - lo) / 3.0;
    float mid2 = hi - (hi - lo) / 3.0;
    float d1 = length(p - path_`).concat(a,`_position(mid1, source, target));
    float d2 = length(p - path_`).concat(a,`_position(mid2, source, target));
    if (d1 < d2) {
      hi = mid2;
    } else {
      lo = mid1;
    }
  }
  return (lo + hi) * 0.5;
}
`)}function jl(a){return`
// Auto-generated signed distance (via closest_t + normal)
float path_`.concat(a,`_distance(vec2 p, vec2 source, vec2 target) {
  float closestT = path_`).concat(a,`_closest_t(p, source, target);
  vec2 closest = path_`).concat(a,`_position(closestT, source, target);
  vec2 diff = p - closest;
  float dist = length(diff);
  if (dist < 0.0001) return 0.0;

  // Get normal at closest point
  vec2 normal = path_`).concat(a,`_normal(closestT, source, target);
  return dist * sign(dot(diff, normal));
}
`)}function ql(a){return`
// Auto-generated t_at_distance (binary search)
float path_`.concat(a,`_t_at_distance(float targetDist, vec2 source, vec2 target) {
  if (targetDist <= 0.0) return 0.0;

  float totalLen = path_`).concat(a,`_length(source, target);
  if (targetDist >= totalLen) return 1.0;

  // Binary search for t
  float lo = 0.0, hi = 1.0;
  for (int i = 0; i < 12; i++) {
    float mid = (lo + hi) * 0.5;

    // Compute arc length from 0 to mid
    float arcLen = 0.0;
    vec2 prev = path_`).concat(a,`_position(0.0, source, target);
    for (int j = 1; j <= 8; j++) {
      float t = mid * float(j) / 8.0;
      vec2 curr = path_`).concat(a,`_position(t, source, target);
      arcLen += length(curr - prev);
      prev = curr;
    }

    if (arcLen < targetDist) {
      lo = mid;
    } else {
      hi = mid;
    }
  }
  return (lo + hi) * 0.5;
}
`)}function mn(a,n){var t=new RegExp("\\b(float|vec[234]|void|int|bool)\\s+".concat(n,"\\s*\\("));return t.test(a)}function ni(a,n){var t=[];return mn(n,"path_".concat(a,"_length"))||t.push(Vl(a)),mn(n,"path_".concat(a,"_closest_t"))||t.push(Xl(a)),mn(n,"path_".concat(a,"_distance"))||t.push(jl(a)),mn(n,"path_".concat(a,"_t_at_distance"))||t.push(ql(a)),t.length>0?`
// ============================================================================
// Auto-generated fallback functions (path only provided position)
// ============================================================================
`.concat(t.join(`
`)):""}function ai(a){var n,t,e,r=a.paths,i=a.layers,o=(n=a.extremities)!==null&&n!==void 0?n:[];if(r.length===0)throw new Error("At least one path is required in 'paths'");if(i.length===0)throw new Error("At least one layer is required in 'layers'");var s=(t=a.defaultHead)!==null&&t!==void 0?t:"none",l=(e=a.defaultTail)!==null&&e!==void 0?e:"none";return{paths:r,extremities:o,layers:i,path:r[0],layer:i[0],defaultHead:s,defaultTail:l}}var ri=WebGL2RenderingContext,Pt=ri.FLOAT,zr=ri.UNSIGNED_BYTE;function Yl(a,n,t){var e=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_zoomRatio","u_pixelRatio","u_cameraAngle","u_minEdgeThickness","u_pickingPadding","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeFrameTexture","u_edgeFrameTextureWidth","u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"]),r=new Set(e);return a.forEach(function(i){return i.uniforms.forEach(function(o){return r.add(o.name)})}),n.forEach(function(i){return i.uniforms.forEach(function(o){return r.add(o.name)})}),t.forEach(function(i){return i.uniforms.forEach(function(o){return r.add(o.name)})}),Array.from(r)}function va(a){var n=new Set,t=[],e=M(a),r;try{for(e.s();!(r=e.n()).done;){var i=r.value;n.has(i.name)||(n.add(i.name),t.push("// Path: ".concat(i.name)),t.push(i.glsl),t.push(ti(i.name)),t.push(ni(i.name,i.glsl)))}}catch(o){e.e(o)}finally{e.f()}return t.join(`

`)}function Kl(a){var n=[],t=M(a),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;n.push("// Extremity: ".concat(r.name)),n.push(r.glsl)}}catch(i){t.e(i)}finally{t.f()}return n.join(`

`)}var Zl=[{queryName:"queryPathPosition",pathFunc:"position",returnType:"vec2",params:"float t, vec2 source, vec2 target",args:"t, source, target"},{queryName:"queryPathTangent",pathFunc:"tangent",returnType:"vec2",params:"float t, vec2 source, vec2 target",args:"t, source, target"},{queryName:"queryPathNormal",pathFunc:"normal",returnType:"vec2",params:"float t, vec2 source, vec2 target",args:"t, source, target"},{queryName:"queryPathLength",pathFunc:"length",returnType:"float",params:"vec2 source, vec2 target",args:"source, target"},{queryName:"queryPathClosestT",pathFunc:"closest_t",returnType:"float",params:"vec2 p, vec2 source, vec2 target",args:"p, source, target"}];function Ql(a,n){var t=n.queryName,e=n.pathFunc,r=n.returnType,i=n.params,o=n.args;if(a.length===1)return"".concat(r," ").concat(t,"(int pathId, ").concat(i,`) {
  return path_`).concat(a[0].name,"_").concat(e,"(").concat(o,`);
}`);var s=a.map(function(l,u){return"    case ".concat(u,": return path_").concat(l.name,"_").concat(e,"(").concat(o,");")}).join(`
`);return"".concat(r," ").concat(t,"(int pathId, ").concat(i,`) {
  switch (pathId) {
`).concat(s,`
    default: return path_`).concat(a[0].name,"_").concat(e,"(").concat(o,`);
  }
}`)}function pa(a){return Zl.map(function(n){return Ql(a,n)}).join(`

`)}function Jl(a){if(a.length===1)return`float queryExtremitySDF(int extremityId, vec2 uv, float lengthRatio, float widthRatio) {
  return extremity_`.concat(a[0].name,`(uv, lengthRatio, widthRatio);
}`);var n=a.map(function(t,e){return"    case ".concat(e,": return extremity_").concat(t.name,"(uv, lengthRatio, widthRatio);")}).join(`
`);return`float queryExtremitySDF(int extremityId, vec2 uv, float lengthRatio, float widthRatio) {
  switch (extremityId) {
`.concat(n,`
    default: return extremity_`).concat(a[0].name,`(uv, lengthRatio, widthRatio);
  }
}`)}function eu(a){var n=[],t=M(a),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;n.push(Hl(r.name)),n.push($l(r.name))}}catch(s){t.e(s)}finally{t.f()}if(a.length===1)n.push(`
float queryFindSourceClampT(int pathId, vec2 source, float sourceSize, int sourceShapeId, float sourceRotateAlign, vec2 target, float margin) {
  return findSourceClampT_`.concat(a[0].name,`(source, sourceSize, sourceShapeId, sourceRotateAlign, target, margin);
}

float queryFindTargetClampT(int pathId, vec2 source, vec2 target, float targetSize, int targetShapeId, float targetRotateAlign, float margin) {
  return findTargetClampT_`).concat(a[0].name,`(source, target, targetSize, targetShapeId, targetRotateAlign, margin);
}`));else{var i=a.map(function(s,l){return"    case ".concat(l,": return findSourceClampT_").concat(s.name,"(source, sourceSize, sourceShapeId, sourceRotateAlign, target, margin);")}).join(`
`),o=a.map(function(s,l){return"    case ".concat(l,": return findTargetClampT_").concat(s.name,"(source, target, targetSize, targetShapeId, targetRotateAlign, margin);")}).join(`
`);n.push(`
float queryFindSourceClampT(int pathId, vec2 source, float sourceSize, int sourceShapeId, float sourceRotateAlign, vec2 target, float margin) {
  switch (pathId) {
`.concat(i,`
    default: return findSourceClampT_`).concat(a[0].name,`(source, sourceSize, sourceShapeId, sourceRotateAlign, target, margin);
  }
}

float queryFindTargetClampT(int pathId, vec2 source, vec2 target, float targetSize, int targetShapeId, float targetRotateAlign, float margin) {
  switch (pathId) {
`).concat(o,`
    default: return findTargetClampT_`).concat(a[0].name,`(source, target, targetSize, targetShapeId, targetRotateAlign, margin);
  }
}`))}return n.join(`

`)}function tu(a,n,t,e,r){var i=me([].concat($(a),$(t))),o=Nt(i),s=ht(e,r),l=Object.keys(s.offsets),u=function(R){var E=s.specs[R].size;return E===1?"float":"vec".concat(E)},d=l.map(function(_){return"".concat(u(_)," v_source_").concat(_,`;
`).concat(u(_)," v_target_").concat(_,";")}).join(`
`),c=lt(s,{varPrefix:"srcNodeAttr",baseTexelExpr:"srcIdx * u_layerAttributeTexelsPerNode",textureWidthUniform:"u_layerAttributeTextureWidth",textureSamplerUniform:"u_layerAttributeTexture",outputPrefix:"v_source_"}),f=lt(s,{varPrefix:"tgtNodeAttr",baseTexelExpr:"tgtIdx * u_layerAttributeTexelsPerNode",textureWidthUniform:"u_layerAttributeTextureWidth",textureSamplerUniform:"u_layerAttributeTexture",outputPrefix:"v_target_"}),h=l.map(function(_){return"".concat(u(_)," g_").concat(_,";")}).join(`
`),g=l.map(function(_){return"  g_".concat(_," = v_source_").concat(_,";")}).join(`
`),m=l.map(function(_){return"  g_".concat(_," = v_target_").concat(_,";")}).join(`
`),p=new Set,v=[],b=function(R){p.has(R.name)||(p.add(R.name),v.push("uniform ".concat(R.type," ").concat(R.name,";")))};a.forEach(function(_){return _.uniforms.forEach(b)}),n.forEach(function(_){return _.uniforms.forEach(b)});var y=n.map(function(_){return ae(_.widthFactor)}).join(", "),T=Math.max.apply(Math,$(a.map(function(_){return _.minBodyLengthRatio||0}))),x=`#version 300 es

// Node and edge data textures
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_edgeDataTexture;
uniform int u_edgeDataTextureWidth;

// Edge attribute texture (for path-specific attributes like curvature)
`.concat(o.uniformDeclarations,`

// Node attribute texture (for node shape attributes)
uniform sampler2D u_layerAttributeTexture;
uniform int u_layerAttributeTextureWidth;
uniform int u_layerAttributeTexelsPerNode;

// Render params needed for clamping
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
uniform float u_minEdgeThickness;

// Edge-frame texture dimensions, for scattering each point to its texel
uniform float u_frameTextureWidth;
uniform float u_frameTextureHeight;

// Custom path/extremity uniforms
`).concat(v.join(`
`),`

// Path attribute varyings \u2014 assigned so path functions can read them as globals
`).concat(o.vertexVaryingDeclarations,`

// Node size varyings \u2014 read by path functions like loop
out float v_sourceNodeSize;
out float v_targetNodeSize;

// Node shape attributes per endpoint, and the ones querySDF reads
`).concat(d,`
`).concat(h,`

// Scattered output written to the edge-frame texel: [tStart, tEnd, straightenFactor, pathLength]
out vec4 v_clamp;

// Extremity width factor array (needed for extremityScale computation)
const float EXTREMITY_WIDTH_FACTORS[`).concat(n.length,"] = float[](").concat(y,`);

// Node-data fetch helpers (geometry texel + rotation-flags texel)
`).concat(Le,`
`).concat(Ue,`

// Shape SDFs for node boundary clamping
`).concat(rl(),`
`).concat(il(new Set(l)),`

// Path functions
`).concat(va(a),`
`).concat(pa(a),`
`).concat(eu(a),`

void main() {
  // One point per edge-data row; the row index is the edge-frame texel target.
  int edgeIdx = gl_VertexID;
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 edgeTexCoord0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 edgeTexCoord1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, edgeTexCoord0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, edgeTexCoord1, 0);

  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float a_thickness = edgeData0.z;
  float a_headLengthRatio = edgeData1.x;
  float a_tailLengthRatio = edgeData1.y;
  int pathId = int(edgeData1.z);
  int extremityPacked = int(edgeData1.w);
  int headId = extremityPacked >> 4;
  int tailId = extremityPacked & 15;

  // Fetch path/layer attributes and assign to path-function globals
`).concat(o.fetchCode,`
`).concat(o.varyingAssignments,`

  // Fetch node shape attributes for both endpoints
`).concat(c.fetchCode,`
`).concat(c.varyingAssignments,`
`).concat(f.fetchCode,`
`).concat(f.varyingAssignments,`

  // Fetch node geometry (texel 0) and rotation flags (texel 1).
  vec4 srcNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 a_source = srcNodeData.xy;
  vec2 a_target = tgtNodeData.xy;
  float a_sourceSize = srcNodeData.z;
  float a_targetSize = tgtNodeData.z;
  float a_sourceShapeId = srcNodeData.w;
  float a_targetShapeId = tgtNodeData.w;
  // Per-node rotation alignment (0 = viewport, 1 = graph), for boundary clamping.
  float a_sourceRotateAlign = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx).r;
  float a_targetRotateAlign = readNodeFlags(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx).r;

  v_sourceNodeSize = a_sourceSize;
  v_targetNodeSize = a_targetSize;

  float headLengthRatio = a_headLengthRatio;
  float tailLengthRatio = a_tailLengthRatio;
  float headWidthFactor = EXTREMITY_WIDTH_FACTORS[headId];
  float tailWidthFactor = EXTREMITY_WIDTH_FACTORS[tailId];
  float minBodyLengthRatio = `).concat(ae(T),`;

  // Thickness in WebGL units (needed to compute clamping margin and extremity lengths)
  float pixelsThickness = max(a_thickness, u_minEdgeThickness * u_sizeRatio);
  float webGLThickness = pixelsThickness * u_correctionRatio / u_sizeRatio;

  // SDF clamping: find where the edge body meets the node boundaries. Always
  // searched (ungated) so labels get a true boundary clamp; the body re-applies
  // its extremity gating in-shader.
`).concat(g,`
  float tStart = queryFindSourceClampT(pathId, a_source, a_sourceSize, int(a_sourceShapeId), a_sourceRotateAlign, a_target, 0.0);
`).concat(m,`
  float tEnd = queryFindTargetClampT(pathId, a_source, a_target, a_targetSize, int(a_targetShapeId), a_targetRotateAlign, 0.0);

  // straightenFactor (frame .z) is consumed only by the body, which runs to the
  // node center when an extremity is absent. Derive the straightening math from
  // these gated clamps \u2014 not the ungated boundary ones above \u2014 so it matches the
  // geometry it drives. The ungated tStart/tEnd remain what labels read.
  float bodyTStart = tailLengthRatio > 0.0 ? tStart : 0.0;
  float bodyTEnd = headLengthRatio > 0.0 ? tEnd : 1.0;

  // Path length and zone boundaries (needed for straightening check)
  float pathLength = queryPathLength(pathId, a_source, a_target);
  float visibleLength = pathLength * (bodyTEnd - bodyTStart);

  float headLength = headLengthRatio * webGLThickness;
  float tailLength = tailLengthRatio * webGLThickness;
  float minBodyLength = minBodyLengthRatio * webGLThickness;

  float totalNeededLength = headLength + tailLength + minBodyLength;
  float extremityScale = 1.0;
  if (totalNeededLength > visibleLength && totalNeededLength > 0.0001) {
    extremityScale = visibleLength / totalNeededLength;
    headLength *= extremityScale;
    tailLength *= extremityScale;
  }

  float headLengthT = pathLength > 0.0001 ? headLength / pathLength : 0.0;
  float tailLengthT = pathLength > 0.0001 ? tailLength / pathLength : 0.0;

  float tTailEnd = bodyTStart + tailLengthT;
  float tHeadStart = bodyTEnd - headLengthT;
  if (tTailEnd > tHeadStart) {
    float mid = (bodyTStart + bodyTEnd) * 0.5;
    tTailEnd = mid;
    tHeadStart = mid;
  }

  // Straighten factor: blend toward straight line when path twists in extremity zones
  float straightenFactor = 0.0;
  {
    float maxDeviation = 0.0;
    if (tailLengthT > 0.0001) {
      vec2 tailTang = queryPathTangent(pathId, tTailEnd, a_source, a_target);
      vec2 tailChord = queryPathPosition(pathId, bodyTStart, a_source, a_target)
                     - queryPathPosition(pathId, tTailEnd, a_source, a_target);
      float tailChordLen = length(tailChord);
      if (tailChordLen > 0.0001) {
        maxDeviation = max(maxDeviation, 1.0 - dot(-tailTang, tailChord / tailChordLen));
      }
    }
    if (headLengthT > 0.0001) {
      vec2 headTang = queryPathTangent(pathId, tHeadStart, a_source, a_target);
      vec2 headChord = queryPathPosition(pathId, bodyTEnd, a_source, a_target)
                     - queryPathPosition(pathId, tHeadStart, a_source, a_target);
      float headChordLen = length(headChord);
      if (headChordLen > 0.0001) {
        maxDeviation = max(maxDeviation, 1.0 - dot(headTang, headChord / headChordLen));
      }
    }
    straightenFactor = smoothstep(0.035, 0.5, maxDeviation);
  }

  // When straightening, blend the ungated tStart/tEnd (the label-facing clamps)
  // toward straight-line clamp positions.
  if (straightenFactor > 0.001) {
    if (tailLengthRatio > 0.0) {
`).concat(g,`
      float srcExtent = a_sourceSize * u_correctionRatio / u_sizeRatio * 2.0;
      float srcEffective = 1.0 - u_correctionRatio / srcExtent;
      float srcCa = u_cameraAngle * (1.0 - a_sourceRotateAlign);
      mat2 srcRot = mat2(cos(srcCa), -sin(srcCa), sin(srcCa), cos(srcCa));
      float lo = 0.0, hi = 0.5;
      for (int i = 0; i < 12; i++) {
        float mid = (lo + hi) * 0.5;
        vec2 pos = mix(a_source, a_target, mid);
        vec2 localPos = srcRot * ((pos - a_source) / srcExtent);
        float sdf = querySDF(int(a_sourceShapeId), localPos, srcEffective);
        if (sdf < 0.0) lo = mid; else hi = mid;
      }
      tStart = mix(tStart, (lo + hi) * 0.5, straightenFactor);
    }
    if (headLengthRatio > 0.0) {
`).concat(m,`
      float tgtExtent = a_targetSize * u_correctionRatio / u_sizeRatio * 2.0;
      float tgtEffective = 1.0 - u_correctionRatio / tgtExtent;
      float tgtCa = u_cameraAngle * (1.0 - a_targetRotateAlign);
      mat2 tgtRot = mat2(cos(tgtCa), -sin(tgtCa), sin(tgtCa), cos(tgtCa));
      float lo = 0.5, hi = 1.0;
      for (int i = 0; i < 12; i++) {
        float mid = (lo + hi) * 0.5;
        vec2 pos = mix(a_source, a_target, mid);
        vec2 localPos = tgtRot * ((pos - a_target) / tgtExtent);
        float sdf = querySDF(int(a_targetShapeId), localPos, tgtEffective);
        if (sdf < 0.0) hi = mid; else lo = mid;
      }
      tEnd = mix(tEnd, (lo + hi) * 0.5, straightenFactor);
    }
  }

  v_clamp = vec4(tStart, tEnd, straightenFactor, pathLength);

  // Scatter this point to its edge's texel center in the frame texture.
  float x = mod(float(edgeIdx), u_frameTextureWidth);
  float y = floor(float(edgeIdx) / u_frameTextureWidth);
  vec2 ndc = (vec2(x, y) + 0.5) / vec2(u_frameTextureWidth, u_frameTextureHeight) * 2.0 - 1.0;
  gl_Position = vec4(ndc, 0.0, 1.0);
  gl_PointSize = 1.0;
}
`);return x}var bn=0,Mr=1,yn=2;function nu(a,n,t){var e=[];t&&(e.push([bn,0,-1],[bn,0,1]),e.push([bn,1,-1],[bn,1,1]));for(var r=0;r<=a;r++){var i=r/a;e.push([Mr,i,-1],[Mr,i,1])}return n&&(e.push([yn,0,-1],[yn,0,1]),e.push([yn,1,-1],[yn,1,1])),{data:e,attributes:[{name:"a_zone",size:1,type:Pt},{name:"a_zoneT",size:1,type:Pt},{name:"a_side",size:1,type:Pt}],verticesPerEdge:e.length}}function au(a,n,t,e){var r=me([].concat($(a),$(t))),i=Nt(r),o=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_zoomRatio","u_pixelRatio","u_cameraAngle","u_minEdgeThickness","u_pickingPadding","u_nodeDataTexture"]),s=new Set,l=[],u=function(v){!o.has(v.name)&&!s.has(v.name)&&(s.add(v.name),l.push("uniform ".concat(v.type," ").concat(v.name,";")))};a.forEach(function(p){return p.uniforms.forEach(u)}),n.forEach(function(p){return p.uniforms.forEach(u)}),t.forEach(function(p){return p.uniforms.forEach(u)});var d=e.map(function(p){var v=p.size===1?"float":"vec".concat(p.size);return"in ".concat(v," ").concat(p.name,";")}).join(`
`),c=n.map(function(p){return ae(p.widthFactor)}).join(", "),f=Math.max.apply(Math,$(a.map(function(p){return p.minBodyLengthRatio||0}))),h=t.some(function(p){return p.needsNodeColors}),g=a.some(function(p){return p.needsNodeSize}),m=`#version 300 es

// Constant attributes (per vertex)
`.concat(d,`

// Per-edge attributes
// Edge data (source/target indices, thickness, extremity ratios, path/extremity IDs)
// is fetched from edge data texture via edge index
in float a_edgeIndex;   // Index into edge data texture
in vec4 a_color;        // Edge color
in vec4 a_id;           // Edge ID for picking
in float a_opacity;     // Edge opacity

// Standard uniforms
uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_zoomRatio;
uniform float u_pixelRatio;
uniform float u_cameraAngle;
uniform float u_minEdgeThickness;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_edgeDataTexture;
uniform int u_edgeDataTextureWidth;
uniform sampler2D u_edgeFrameTexture;
uniform int u_edgeFrameTextureWidth;

// Edge path attribute texture uniforms
`).concat(i.uniformDeclarations,`

// Custom uniforms
`).concat(l.join(`
`),`

// Standard varyings
out vec4 v_color;
out float v_opacity;
out vec4 v_id;
out float v_thickness;       // Edge body thickness (in consistent units)
out float v_t;
out float v_tStart;
out float v_tEnd;
out float v_side;
out float v_antialiasingWidth;  // Anti-aliasing width (normalized: u_correctionRatio / thickness)
out vec2 v_source;
out vec2 v_target;
out float v_edgeLength;
`).concat(g?`
out float v_sourceNodeSize;  // Source node size (mirrored in labels/generator.ts as plain float)
out float v_targetNodeSize;  // Target node size (mirrored in labels/generator.ts as plain float)`:"",`
`).concat(h?`
out vec4 v_sourceColor;
out vec4 v_targetColor;`:"",`
// Zone varyings
out float v_zone;            // 0=tail, 1=body, 2=head
out float v_zoneT;           // Position within zone [0,1]
out float v_headLengthRatio; // Head length as ratio of thickness
out float v_tailLengthRatio; // Tail length as ratio of thickness
out float v_headWidthRatio;  // Head width factor
out float v_tailWidthRatio;  // Tail width factor

// Multi-path/extremity varyings
flat out int v_pathId;
flat out int v_headId;
flat out int v_tailId;

// Path/layer attribute varyings (fetched from edge attribute texture)
`).concat(i.vertexVaryingDeclarations,`

const float bias = 255.0 / 254.0;

// Width factor array for extremities (shared pool for head/tail)
const float EXTREMITY_WIDTH_FACTORS[`).concat(n.length,"] = float[](").concat(c,`);

// All path functions
`).concat(va(a),`

// Path selector functions
`).concat(pa(a),`

// Node-data fetch helper (geometry texel of the two-texel node stride)
`).concat(Le,`
`).concat(h?hl:"",`
// Per-edge clamp from the frame-pass (tStart, tEnd, straightenFactor, pathLength)
`).concat(ct,`

void main() {
  // Fetch edge data from edge texture (2 texels per edge)
  // Texel 0: sourceNodeIndex, targetNodeIndex, thickness, reserved
  // Texel 1: headLengthRatio, tailLengthRatio, pathId, (headId << 4) | tailId
  int edgeIdx = int(a_edgeIndex);

  // Hidden edges are flagged with a negative row by EdgeProgram.process(). Push
  // the whole primitive outside the clip volume: every vertex lands at the same
  // out-of-range position, so it is fully clipped and rasterizes nothing \u2014
  // neither to the frame buffer nor to the picking buffer.
  if (edgeIdx < 0) {
    gl_Position = vec4(2.0, 0.0, 0.0, 1.0);
    v_color = vec4(0.0);
    v_id = vec4(0.0);
    return;
  }

  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 edgeTexCoord0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 edgeTexCoord1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, edgeTexCoord0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, edgeTexCoord1, 0);

  // Unpack edge data
  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float a_thickness = edgeData0.z;
  // edgeData0.w is now reserved (curvature moved to path attribute texture)
  float a_headLengthRatio = edgeData1.x;
  float a_tailLengthRatio = edgeData1.y;
  int pathId = int(edgeData1.z);
  int extremityPacked = int(edgeData1.w);
  int headId = extremityPacked >> 4;
  int tailId = extremityPacked & 15;

  // Fetch path/layer attributes from edge attribute texture
`).concat(i.fetchCode,`

  // Assign path/layer attribute varyings
`).concat(i.varyingAssignments,`

  // Fetch source and target node geometry (texel 0 of the two-texel node stride)
  vec4 srcNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 a_source = srcNodeData.xy;
  vec2 a_target = tgtNodeData.xy;
`).concat(g?`
  // Assign node size varyings early (path functions like loops need them during clamping)
  v_sourceNodeSize = srcNodeData.z;
  v_targetNodeSize = tgtNodeData.z;`:"",`
`).concat(h?`
  v_sourceColor = readNodeColor(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  v_targetColor = readNodeColor(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);`:"",`

  // Convert thickness to WebGL units
  float minThickness = u_minEdgeThickness;
  float pixelsThickness = max(a_thickness, minThickness * u_sizeRatio);
  float webGLThickness = pixelsThickness * u_correctionRatio / u_sizeRatio;

  // Extremity parameters from ID lookups (shared pool)
  float headLengthRatio = a_headLengthRatio;
  float tailLengthRatio = a_tailLengthRatio;
  float headWidthFactor = EXTREMITY_WIDTH_FACTORS[headId];
  float tailWidthFactor = EXTREMITY_WIDTH_FACTORS[tailId];
  float minBodyLengthRatio = `).concat(ae(f),`;

  // Per-edge values from the frame-pass texture (read by edge index).
  // tStart/tEnd are the ungated boundary clamps: re-apply the body's extremity
  // gating here (no extremity \u2192 body runs to the node center, 0/1).
  vec4 frameClamp = readFrameTexel(u_edgeFrameTexture, u_edgeFrameTextureWidth, edgeIdx);
  float tStart           = a_tailLengthRatio > 0.0 ? frameClamp.x : 0.0;
  float tEnd             = a_headLengthRatio > 0.0 ? frameClamp.y : 1.0;
  float straightenFactor = frameClamp.z;
  float pathLength       = frameClamp.w;

  // Anti-aliasing width (~1 pixel, normalized by thickness)
  float antialiasingWidth = u_correctionRatio / webGLThickness;

  float visibleLength = pathLength * (tEnd - tStart);

  // Compute extremity lengths in world units
  float headLength = headLengthRatio * webGLThickness;
  float tailLength = tailLengthRatio * webGLThickness;
  float minBodyLength = minBodyLengthRatio * webGLThickness;

  // Handle short edges: scale down extremities if needed
  float totalNeededLength = headLength + tailLength + minBodyLength;
  float extremityScale = 1.0;
  if (totalNeededLength > visibleLength && totalNeededLength > 0.0001) {
    extremityScale = visibleLength / totalNeededLength;
    headLength *= extremityScale;
    tailLength *= extremityScale;
  }

  // Convert lengths to t-values
  float headLengthT = pathLength > 0.0001 ? headLength / pathLength : 0.0;
  float tailLengthT = pathLength > 0.0001 ? tailLength / pathLength : 0.0;

  // Zone boundaries in t-space
  float tTailEnd = tStart + tailLengthT;
  float tHeadStart = tEnd - headLengthT;

  // Ensure body has non-negative length
  if (tTailEnd > tHeadStart) {
    float mid = (tStart + tEnd) * 0.5;
    tTailEnd = mid;
    tHeadStart = mid;
  }

  // Convert to webGL units for geometry expansion
  float aaWidthWebGL = antialiasingWidth * webGLThickness;

  // Extra geometry width for picking padding (0 in visual mode)
  #ifdef PICKING_MODE
    float pickingPaddingWebGL = u_pickingPadding * u_correctionRatio;
  #else
    float pickingPaddingWebGL = 0.0;
  #endif

  // Straight-line direction and normal (for blending when straightenFactor > 0)
  vec2 straightDir = length(a_target - a_source) > 0.0001
    ? normalize(a_target - a_source) : vec2(1.0, 0.0);
  vec2 straightNormal = vec2(-straightDir.y, straightDir.x);

  // Zone-based vertex processing using path selectors
  vec2 position;
  vec2 normal;
  float t;
  float zone = a_zone;
  float zoneT = a_zoneT;
  float side = a_side;

  // Scaled extremity width factors (geometry must be at least as wide as body)
  float scaledTailWidth = max(tailWidthFactor * extremityScale, 1.0);
  float scaledHeadWidth = max(headWidthFactor * extremityScale, 1.0);

  if (zone < 0.5) {
    // TAIL ZONE: rectangular quad with scaled width
    vec2 tang = queryPathTangent(pathId, tTailEnd, a_source, a_target);
    normal = vec2(-tang.y, tang.x);
    vec2 centerPos = mix(queryPathPosition(pathId, tStart, a_source, a_target),
                         queryPathPosition(pathId, tTailEnd, a_source, a_target), zoneT);
    float halfWidth = webGLThickness * scaledTailWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    position = centerPos + normal * side * halfWidth;
    t = mix(tStart, tTailEnd, zoneT);

  } else if (zone < 1.5) {
    // BODY ZONE: follows path curvature with width = 1.0
    t = mix(tTailEnd, tHeadStart, zoneT);
    normal = queryPathNormal(pathId, t, a_source, a_target);
    float halfWidth = webGLThickness * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    position = queryPathPosition(pathId, t, a_source, a_target) + normal * side * halfWidth;

  } else {
    // HEAD ZONE: rectangular quad with scaled width
    vec2 tang = queryPathTangent(pathId, tHeadStart, a_source, a_target);
    normal = vec2(-tang.y, tang.x);
    vec2 centerPos = mix(queryPathPosition(pathId, tHeadStart, a_source, a_target),
                         queryPathPosition(pathId, tEnd, a_source, a_target), zoneT);
    float halfWidth = webGLThickness * scaledHeadWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    position = centerPos + normal * side * halfWidth;
    t = mix(tHeadStart, tEnd, zoneT);
  }

  // Blend toward straight line based on path twist in extremity zones
  if (straightenFactor > 0.001) {
    float zoneWidth = zone < 0.5 ? webGLThickness * scaledTailWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL :
                      zone < 1.5 ? webGLThickness * 0.5 + aaWidthWebGL + pickingPaddingWebGL :
                      webGLThickness * scaledHeadWidth * 0.5 + aaWidthWebGL + pickingPaddingWebGL;
    vec2 straightPos = mix(a_source, a_target, t) + straightNormal * side * zoneWidth;
    position = mix(position, straightPos, straightenFactor);
  }

  gl_Position = vec4((u_matrix * vec3(position, 1.0)).xy, 0.0, 1.0);

  // Pass varyings to fragment shader
  v_color = a_color;
  v_color.a *= bias;
  v_opacity = a_opacity;
  v_id = a_id;
  v_thickness = webGLThickness;
  v_t = t;
  v_tStart = tStart;
  v_tEnd = tEnd;
  v_side = side;
  v_antialiasingWidth = antialiasingWidth;
  v_source = a_source;
  v_target = a_target;
  v_edgeLength = pathLength;

  // Zone varyings
  v_zone = zone;
  v_zoneT = zoneT;
  v_headLengthRatio = headLengthRatio * extremityScale;
  v_tailLengthRatio = tailLengthRatio * extremityScale;
  // Scale extremity width proportionally with length when crushed
  v_headWidthRatio = headWidthFactor * extremityScale;
  v_tailWidthRatio = tailWidthFactor * extremityScale;

  // Multi-path varyings
  v_pathId = pathId;
  v_headId = headId;
  v_tailId = tailId;
}
`);return m}function ru(a,n,t,e){var r=me([].concat($(a),$(t))),i=Nt(r),o=new Set(["u_matrix","u_sizeRatio","u_correctionRatio","u_zoomRatio","u_pixelRatio","u_cameraAngle","u_minEdgeThickness","u_pickingPadding"]),s=new Set,l=[],u=function(b){!o.has(b.name)&&!s.has(b.name)&&(s.add(b.name),l.push("uniform ".concat(b.type," ").concat(b.name,";")))};a.forEach(function(v){return v.uniforms.forEach(u)}),n.forEach(function(v){return v.uniforms.forEach(u)}),t.forEach(function(v){return v.uniforms.forEach(u)});var d=n.map(function(v){var b;return ae((b=v.baseRatio)!==null&&b!==void 0?b:.5)}).join(", "),c=function(b){var y,T;return n.length>1?"EXTREMITY_BASE_RATIOS[".concat(b,"]"):ae((y=(T=n[0])===null||T===void 0?void 0:T.baseRatio)!==null&&y!==void 0?y:.5)},f=n.some(function(v){return _e(v.length)?!0:v.length>0}),h=t.some(function(v){return v.needsNodeColors}),g=a.some(function(v){return v.needsNodeSize}),m=t.map(function(v,b){return"  // Layer ".concat(b+1,": ").concat(v.name,`
  color = blendOver(color, layer_`).concat(v.name,"(context));")}).join(`

`),p=`#version 300 es
precision highp float;

// Standard varyings
in vec4 v_color;
in float v_opacity;
in vec4 v_id;
in float v_thickness;       // Edge body thickness
in float v_t;
in float v_tStart;
in float v_tEnd;
in float v_side;
in float v_antialiasingWidth;  // Anti-aliasing width (normalized: u_correctionRatio / thickness)
in vec2 v_source;
in vec2 v_target;
in float v_edgeLength;
`.concat(g?`
in float v_sourceNodeSize;   // Source node size (mirrored in labels/generator.ts as plain float)
in float v_targetNodeSize;   // Target node size (mirrored in labels/generator.ts as plain float)`:"",`
`).concat(h?`
in vec4 v_sourceColor;
in vec4 v_targetColor;`:"",`
// Zone varyings
in float v_zone;            // 0=tail, 1=body, 2=head
in float v_zoneT;           // Position within zone [0,1]
in float v_headLengthRatio; // Head length as ratio of thickness (scaled for short edges)
in float v_tailLengthRatio; // Tail length as ratio of thickness (scaled for short edges)
in float v_headWidthRatio;  // Head width factor
in float v_tailWidthRatio;  // Tail width factor

// Multi-path/extremity varyings
flat in int v_pathId;
flat in int v_headId;
flat in int v_tailId;

// Path/layer attribute varyings (from vertex shader texture fetch)
`).concat(i.fragmentVaryingDeclarations,`

// Standard uniforms (needed by some path types)
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_cameraAngle;
#ifdef PICKING_MODE
uniform float u_pickingPadding;
#endif

// Custom uniforms
`).concat(l.join(`
`),`

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

`).concat(n.length>1?`// Base ratio array for extremities (shared pool for head/tail)
const float EXTREMITY_BASE_RATIOS[`.concat(n.length,"] = float[](").concat(d,");"):"",`

// EdgeContext struct
struct EdgeContext {
  float t;                   // Position along path [0, 1]
  float sdf;                 // Signed distance from centerline
  vec2 position;             // World position
  vec2 tangent;              // Path tangent
  vec2 normal;               // Path normal
  float thickness;           // Edge thickness
  float aaWidth;             // Anti-aliasing width
  float edgeLength;          // Total path length
  float tStart;              // Clamped start t
  float tEnd;                // Clamped end t
  float distanceFromSource;  // Arc distance from source
  float distanceToTarget;    // Arc distance to target
};

EdgeContext context;

// Alpha "over" compositing for layer blending
vec4 blendOver(vec4 bg, vec4 fg) {
  float a = fg.a;
  return vec4(mix(bg.rgb, fg.rgb, a), bg.a + a * (1.0 - bg.a));
}

// All path functions
`).concat(va(a),`

// Path selector functions
`).concat(pa(a),`

// All extremity functions
`).concat(Kl(n),`

// Extremity SDF selector (shared pool for head/tail)
`).concat(Jl(n),`

// Layer functions
`).concat(t.map(function(v){return v.glsl}).join(`

`),`

// Helper: Compute arc length using path selector
float computeArcLengthMulti(int pathId, float t0, float t1, vec2 source, vec2 target, int samples) {
  float arcLen = 0.0;
  vec2 prev = queryPathPosition(pathId, t0, source, target);
  for (int i = 1; i <= samples; i++) {
    float t = t0 + (t1 - t0) * float(i) / float(samples);
    vec2 curr = queryPathPosition(pathId, t, source, target);
    arcLen += length(curr - prev);
    prev = curr;
  }
  return arcLen;
}

void main() {
  // Compute normalized t within visible edge (0 = start, 1 = end)
  float tNorm = (v_t - v_tStart) / max(v_tEnd - v_tStart, 0.0001);

  // Edge body half-thickness
  float halfThickness = v_thickness * 0.5;

  // Convert normalized AA width to webGL units (~1 pixel)
  float aaWidthWebGL = v_antialiasingWidth * v_thickness;

  // Distance from centerline based on v_side interpolation
  float zoneWidthFactor = v_zone < 0.5 ? v_tailWidthRatio :
                          v_zone < 1.5 ? 1.0 :
                          v_headWidthRatio;
  // In PICKING_MODE, inflate halfGeometryWidth to match the inflated vertex geometry
  #ifdef PICKING_MODE
    float halfGeometryWidth = halfThickness * zoneWidthFactor + aaWidthWebGL + u_pickingPadding * aaWidthWebGL;
  #else
    float halfGeometryWidth = halfThickness * zoneWidthFactor + aaWidthWebGL;
  #endif
  float distFromCenter = abs(v_side) * halfGeometryWidth;

  // Populate EdgeContext (for layer functions)
  context.t = tNorm;
  context.sdf = distFromCenter - halfThickness;
  context.position = queryPathPosition(v_pathId, v_t, v_source, v_target);
  context.tangent = queryPathTangent(v_pathId, v_t, v_source, v_target);
  context.normal = vec2(-context.tangent.y, context.tangent.x);
  context.thickness = v_thickness;
  context.aaWidth = aaWidthWebGL;
  context.edgeLength = v_edgeLength;
  context.tStart = v_tStart;
  context.tEnd = v_tEnd;

  // Compute arc distances
  float visibleLength = v_edgeLength * (v_tEnd - v_tStart);
  float pathT = v_t;
  float pathTNorm = tNorm;
`).concat(a.every(function(v){return v.linearParameterization})?`  // All paths have linear parameterization: t maps directly to arc distance
  context.distanceFromSource = pathTNorm * visibleLength;
  context.distanceToTarget = (1.0 - pathTNorm) * visibleLength;`:a.every(function(v){return!v.linearParameterization})?`  // No paths have linear parameterization: use numerical integration
  context.distanceFromSource = computeArcLengthMulti(v_pathId, v_tStart, pathT, v_source, v_target, 16);
  context.distanceToTarget = computeArcLengthMulti(v_pathId, pathT, v_tEnd, v_source, v_target, 16);`:`  // Mixed parameterization: use analytical for linear paths, numerical for others
  if (`.concat(a.filter(function(v){return v.linearParameterization}).map(function(v){return"v_pathId == ".concat(a.indexOf(v))}).join(" || "),`) {
    context.distanceFromSource = pathTNorm * visibleLength;
    context.distanceToTarget = (1.0 - pathTNorm) * visibleLength;
  } else {
    context.distanceFromSource = computeArcLengthMulti(v_pathId, v_tStart, pathT, v_source, v_target, 16);
    context.distanceToTarget = computeArcLengthMulti(v_pathId, pathT, v_tEnd, v_source, v_target, 16);
  }`),`

  // Compute SDF based on zone using extremity selector (shared pool)
  float bodySDF = distFromCenter - halfThickness;
  float finalSDF;

`).concat(f?`  // Base ratios, from baseRatioLookup
  float headBaseRatio = `.concat(c("v_headId"),`;
  float tailBaseRatio = `).concat(c("v_tailId"),`;

  if (v_zone < 0.5) {
    // TAIL ZONE: v_zoneT goes 0 (tip) to 1 (base)
    vec2 uv = vec2((1.0 - v_zoneT) * v_tailLengthRatio, v_side * v_tailWidthRatio * 0.5);
    float tailSDF = queryExtremitySDF(v_tailId, uv, v_tailLengthRatio, v_tailWidthRatio) * v_thickness;

    // Apply union only near base (v_zoneT > 1 - baseRatio)
    if (v_zoneT > 1.0 - tailBaseRatio) {
      finalSDF = min(tailSDF, bodySDF);
    } else {
      finalSDF = tailSDF;
    }
  } else if (v_zone < 1.5) {
    // BODY ZONE: distance from centerline
    finalSDF = bodySDF;
  } else {
    // HEAD ZONE: v_zoneT goes 0 (base) to 1 (tip)
    vec2 uv = vec2(v_zoneT * v_headLengthRatio, v_side * v_headWidthRatio * 0.5);
    float headSDF = queryExtremitySDF(v_headId, uv, v_headLengthRatio, v_headWidthRatio) * v_thickness;

    // Apply union only near base (v_zoneT < baseRatio)
    if (v_zoneT < headBaseRatio) {
      finalSDF = min(headSDF, bodySDF);
    } else {
      finalSDF = headSDF;
    }
  }`):`  // No extremity draws tail/head geometry, so every vertex is body zone.
  finalSDF = bodySDF;`,`

  #ifdef PICKING_MODE
    // Picking pass: output edge ID for pixels within the picking area
    if (finalSDF > u_pickingPadding * aaWidthWebGL) discard;
    fragColor = v_id;
  #else
`).concat(e?`    // Visual pass: anti-aliased edge with layers, edge opacity applied once
    float alpha = smoothstep(aaWidthWebGL, -aaWidthWebGL, finalSDF) * v_opacity;`:`    // Visual pass: hard-edged (no anti-aliasing gradient) edge with layers, edge opacity applied once
    float alpha = (finalSDF < 0.0 ? 1.0 : 0.0) * v_opacity;`,`
    if (alpha < 0.01) discard;

    // Apply layers sequentially with "over" compositing
    vec4 color = vec4(0.0);

`).concat(m,`

    // Mix with transparent to fade both color AND alpha (pre-multiplied alpha for correct blending)
    fragColor = mix(vec4(0.0), color, alpha);
  #endif
}
`);return p}function iu(a,n,t){var e=_e(n.length)?!0:n.length>0,r=_e(t.length)?!0:t.length>0;if(a.generateConstantData){var i=a.generateConstantData();return{data:i.data,attributes:i.attributes,verticesPerEdge:i.verticesPerEdge}}return nu(a.segments,e,r)}function Br(a){var n,t=ai(a),e=t.paths,r=t.extremities,i=t.layers,o=(n=a.antialias)!==null&&n!==void 0?n:!0,s=new Map,l=new Map,u=new Map,d=M(e),c;try{for(d.s();!(c=d.n()).done;){var f=c.value,h=M(r),g;try{for(h.s();!(g=h.n()).done;){var m=g.value,p=M(r),v;try{for(p.s();!(v=p.n()).done;){var b=v.value,y="".concat(f.name,":").concat(m.name,":").concat(b.name),T=iu(f,m,b);s.set(y,T.verticesPerEdge),l.set(y,T.data);var x=M(T.attributes),_;try{for(x.s();!(_=x.n()).done;){var R=_.value;u.has(R.name)||u.set(R.name,R)}}catch(X){x.e(X)}finally{x.f()}}}catch(X){p.e(X)}finally{p.f()}}}catch(X){h.e(X)}finally{h.f()}}}catch(X){d.e(X)}finally{d.f()}var E=Array.from(u.values()),L={};E.forEach(function(X,j){L[X.name]=j});var D=0,F="",A=M(s),I;try{for(A.s();!(I=A.n()).done;){var w=Q(I.value,2),k=w[0],G=w[1];G>D&&(D=G,F=k)}}catch(X){A.e(X)}finally{A.f()}var N=l.get(F)||[],P=F.split(":"),C=Q(P,1),z=C[0],H=e.find(function(X){return X.name===z}),U=[];H!=null&&H.generateConstantData?U=H.generateConstantData().attributes:U=[{name:"a_zone"},{name:"a_zoneT"},{name:"a_side"}];var q=N.map(function(X){var j=new Array(E.length).fill(0);return U.forEach(function(be,le){var Re=L[be.name];Re!==void 0&&le<X.length&&(j[Re]=X[le])}),j});return{vertexShader:au(e,r,i,E),fragmentShader:ru(e,r,i,o),uniforms:Yl(e,r,i),attributes:ou(),verticesPerEdge:D,constantData:q,constantAttributes:E,vertexCountsPerCombination:s,constantDataPerCombination:l}}function ou(a,n,t){return[{name:"a_edgeIndex",size:1,type:Pt},{name:"a_color",size:4,type:zr,normalized:!0},{name:"a_id",size:4,type:zr,normalized:!0},{name:"a_opacity",size:1,type:Pt}]}var su=`#version 300 es
precision highp float;

in vec4 v_clamp;

// RGBA32F target: stores (tStart, tEnd, straightenFactor, pathLength).
out vec4 fragColor;

void main() {
  fragColor = v_clamp;
}
`,lu=function(){function a(n,t){Y(this,a),S(this,"uniformLocations",{});var e=t.paths,r=t.extremities,i=t.layers,o=t.nodeShapes,s=t.nodeLayers;this.gl=n,this.hasAttributeData=me([].concat($(e),$(i))).floatsPerItem>0,this.hasNodeAttributeData=Object.keys(ht(o,s).offsets).length>0,this.vertexShader=la(n,tu(e,r,i,o,s)),this.fragmentShader=ua(n,su),this.program=da(n,[this.vertexShader,this.fragmentShader]);var l=new Set;this.customUniforms=[];for(var u=0,d=[].concat($(e),$(r));u<d.length;u++){var c=d[u],f=M(c.uniforms),h;try{for(f.s();!(h=f.n()).done;){var g=h.value;l.has(g.name)||(l.add(g.name),this.customUniforms.push(g))}}catch(y){f.e(y)}finally{f.f()}}var m=["u_sizeRatio","u_correctionRatio","u_cameraAngle","u_minEdgeThickness","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge","u_layerAttributeTexture","u_layerAttributeTextureWidth","u_layerAttributeTexelsPerNode","u_frameTextureWidth","u_frameTextureHeight"].concat($(this.customUniforms.map(function(y){return y.name}))),p=M(m),v;try{for(p.s();!(v=p.n()).done;){var b=v.value;this.uniformLocations[b]=n.getUniformLocation(this.program,b)}}catch(y){p.e(y)}finally{p.f()}this.vao=n.createVertexArray()}return K(a,[{key:"run",value:function(t,e,r,i,o){if(r!==0){var s=this.gl,l=this.uniformLocations;s.useProgram(this.program),s.bindVertexArray(this.vao),l.u_sizeRatio&&s.uniform1f(l.u_sizeRatio,t.sizeRatio),l.u_correctionRatio&&s.uniform1f(l.u_correctionRatio,t.correctionRatio),l.u_cameraAngle&&s.uniform1f(l.u_cameraAngle,t.cameraAngle),l.u_minEdgeThickness&&s.uniform1f(l.u_minEdgeThickness,t.minEdgeThickness),l.u_nodeDataTexture&&s.uniform1i(l.u_nodeDataTexture,t.nodeDataTextureUnit),l.u_nodeDataTextureWidth&&s.uniform1i(l.u_nodeDataTextureWidth,t.nodeDataTextureWidth),l.u_edgeDataTexture&&s.uniform1i(l.u_edgeDataTexture,t.edgeDataTextureUnit),l.u_edgeDataTextureWidth&&s.uniform1i(l.u_edgeDataTextureWidth,t.edgeDataTextureWidth),l.u_frameTextureWidth&&s.uniform1f(l.u_frameTextureWidth,e.getTextureWidth()),l.u_frameTextureHeight&&s.uniform1f(l.u_frameTextureHeight,e.getTextureHeight()),this.hasAttributeData&&i&&(i.bind(Ne),l.u_edgeAttributeTexture&&s.uniform1i(l.u_edgeAttributeTexture,Ne),l.u_edgeAttributeTextureWidth&&s.uniform1i(l.u_edgeAttributeTextureWidth,i.getTextureWidth()),l.u_edgeAttributeTexelsPerEdge&&s.uniform1i(l.u_edgeAttributeTexelsPerEdge,i.getTexelsPerItem())),this.hasNodeAttributeData&&o&&(o.bind(Ie),l.u_layerAttributeTexture&&s.uniform1i(l.u_layerAttributeTexture,Ie),l.u_layerAttributeTextureWidth&&s.uniform1i(l.u_layerAttributeTextureWidth,o.getTextureWidth()),l.u_layerAttributeTexelsPerNode&&s.uniform1i(l.u_layerAttributeTexelsPerNode,o.getTexelsPerItem()));var u=M(this.customUniforms),d;try{for(u.s();!(d=u.n()).done;){var c=d.value;ga(s,this.uniformLocations[c.name],c)}}catch(f){u.e(f)}finally{u.f()}e.bindAsRenderTarget(),s.disable(s.BLEND),s.disable(s.DEPTH_TEST),s.drawArrays(s.POINTS,0,r),s.bindFramebuffer(s.FRAMEBUFFER,null),s.bindVertexArray(null)}}},{key:"kill",value:function(){var t=this.gl;t.deleteProgram(this.program),t.deleteShader(this.vertexShader),t.deleteShader(this.fragmentShader),t.deleteVertexArray(this.vao)}}])}();function Lt(a,n,t,e,r,i){if(a.length===1)return"".concat(e," ").concat(n,"(int pathId, ").concat(r,`) {
  return path_`).concat(a[0].name,"_").concat(t,"(").concat(i,`);
}`);var o=a.map(function(s,l){return"    case ".concat(l,": return path_").concat(s.name,"_").concat(t,"(").concat(i,");")}).join(`
`);return"".concat(e," ").concat(n,"(int pathId, ").concat(r,`) {
  switch (pathId) {
`).concat(o,`
    default: return path_`).concat(a[0].name,"_").concat(t,"(").concat(i,`);
  }
}`)}var uu=`
vec3 computeEdgeLabelBodyBounds(
  float tStart, float tEnd, float pathLength,
  float webGLThickness, float headLengthRatio, float tailLengthRatio
) {
  float visibleLength = pathLength * (tEnd - tStart);

  float headLength = headLengthRatio * webGLThickness;
  float tailLength = tailLengthRatio * webGLThickness;
  float totalNeededLength = headLength + tailLength;
  if (totalNeededLength > visibleLength && totalNeededLength > 0.0001) {
    float extremityScale = visibleLength / totalNeededLength;
    headLength *= extremityScale;
    tailLength *= extremityScale;
  }

  float bodyStartDist = tStart * pathLength + tailLength;
  float bodyEndDist = tEnd * pathLength - headLength;
  return vec3(bodyStartDist, bodyEndDist, max(bodyEndDist - bodyStartDist, 0.0));
}
`;function du(a,n){var t=ae(a),e=ae(n);return`
float computeEdgeLabelAlpha(float bodyLength, float textWidthWebGL) {
  float ratio = textWidthWebGL > 0.0001 ? min(bodyLength / textWidthWebGL, 1.0) : 1.0;
  if (ratio < `.concat(t,`) return 0.0;
  if (ratio < `).concat(e,") return (ratio - ").concat(t,") / (").concat(e," - ").concat(t,`);
  return 1.0;
}
`)}var cu=`
float computeEdgeLabelScreenDir(int pathId, float t, vec2 source, vec2 target, mat3 matrix) {
  vec2 tangent = queryPathTangent(pathId, t, source, target);
  return (matrix * vec3(tangent, 0.0)).x < 0.0 ? -1.0 : 1.0;
}
`,hu=`
float computeEdgeLabelPerpOffset(
  float positionMode,
  float halfThickness, float marginWebGL, float halfTextHeight,
  float readingSign, float screenDir
) {
  float magnitude = halfThickness + marginWebGL + halfTextHeight;
  if (positionMode == 1.0) return magnitude * readingSign;
  if (positionMode == 2.0) return -magnitude * readingSign;
  if (positionMode == 3.0) return magnitude * screenDir;
  return 0.0;
}
`;function ii(a){var n=a.paths,t=a.minVisibilityThreshold,e=a.fullVisibilityThreshold,r=n.some(function(s){return s.hasSharpCorners}),i=n.map(function(s){return"// --- Path: ".concat(s.name,` ---
`).concat(s.glsl,`

// Tangent/normal functions: analytical if provided, otherwise numerical
`).concat(s.analyticalTangentGlsl||ti(s.name),`

// Auto-generated fallbacks for any missing path functions
`).concat(ni(s.name,s.glsl),`

// Corner skip helpers (for paths with sharp corners like step/taxi)
`).concat(s.cornerSkipGlsl||"",`
`)}).join(`
`),o=r?`// Corner function selectors (only some paths have sharp corners)
vec2 queryGetCornerTs(int pathId, vec2 source, vec2 target) {
  switch (pathId) {
`.concat(n.map(function(s,l){return s.hasSharpCorners?"    case ".concat(l,": return path_").concat(s.name,"_getCornerTs(source, target);"):"    case ".concat(l,": return vec2(-1.0, -1.0); // No corners for ").concat(s.name)}).join(`
`),`
    default: return vec2(-1.0, -1.0);
  }
}

vec2 queryGetCornerConcavity(int pathId, vec2 source, vec2 target, float perpOffset) {
  switch (pathId) {
`).concat(n.map(function(s,l){return s.hasSharpCorners?"    case ".concat(l,": return path_").concat(s.name,"_getCornerConcavity(source, target, perpOffset);"):"    case ".concat(l,": return vec2(0.0, 0.0); // No corners for ").concat(s.name)}).join(`
`),`
    default: return vec2(0.0, 0.0);
  }
}`):"";return`
// ============================================================================
// Node data fetch (geometry texel) and per-edge clamp fetch (edge-frame texture)
// ============================================================================

`.concat(Le,`
`).concat(ct,`

// ============================================================================
// Path Functions (one block per path)
// ============================================================================

`).concat(i,`

// ============================================================================
// Path Query Selectors (dispatch by pathId)
// ============================================================================

`).concat(Lt(n,"queryPathPosition","position","vec2","float t, vec2 source, vec2 target","t, source, target"),`

`).concat(Lt(n,"queryPathTangent","tangent","vec2","float t, vec2 source, vec2 target","t, source, target"),`

`).concat(Lt(n,"queryPathNormal","normal","vec2","float t, vec2 source, vec2 target","t, source, target"),`

`).concat(Lt(n,"queryPathLength","length","float","vec2 source, vec2 target","source, target"),`

`).concat(Lt(n,"queryPathTAtDistance","t_at_distance","float","float dist, vec2 source, vec2 target","dist, source, target"),`

`).concat(o,`

// ============================================================================
// Shared helpers (body bounds, alpha ramp, screen direction, perpendicular offset)
// ============================================================================

`).concat(uu,`
`).concat(du(t,e),`
`).concat(cu,`
`).concat(hu,`
`)}var fu=Se.fontSize,gu=new Map,oi=24,Wr=(oi+1)*2;function vu(a){var n=a.paths,t=a.fontSizeMode,e=a.headLengthRatio,r=a.tailLengthRatio,i=a.minVisibilityThreshold,o=a.fullVisibilityThreshold,s=a.keepUpright,l=t==="scaled",u=Te(),d=me([].concat($(n),[u])),c=Nt(d),f=`#version 300 es

// Per-instance attributes
in float a_edgeIndex;
in float a_edgeAttrIndex;
in float a_baseFontSize;
in float a_totalTextWidth;
in float a_positionMode;
in float a_margin;
in float a_padding;
in vec4 a_color;
in vec4 a_id;

// Per-vertex (constant) attribute: strip vertex index
in float a_vertexIndex;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_pixelRatio;
uniform float u_cameraAngle;
uniform vec2 u_resolution;
uniform sampler2D u_nodeDataTexture;
uniform int u_nodeDataTextureWidth;
uniform sampler2D u_edgeDataTexture;
uniform int u_edgeDataTextureWidth;
uniform sampler2D u_edgeFrameTexture; // Per-edge clamp (tStart, tEnd, straightenFactor, pathLength)
uniform int u_edgeFrameTextureWidth;
`.concat(l?"uniform float u_zoomSizeRatio;":"",`

`).concat(c.uniformDeclarations,`

out vec4 v_color;
out vec4 v_id;
out float v_alphaModifier;

const float ATLAS_FONT_SIZE = `).concat(ae(fu),`;
const float HEAD_RATIO = `).concat(ae(e),`;
const float TAIL_RATIO = `).concat(ae(r),`;
const int RIBBON_SEGMENTS = `).concat(oi,`;

// Path attribute varyings (declared as plain locals since this shader has no FS inputs for them)
`).concat(c.vertexVaryingDeclarations.replace(/out /g,""),`

// Node size variables used by some path functions (self-loops, etc.)
float v_sourceNodeSize;
float v_targetNodeSize;

// Shared preamble: shape SDFs, path functions + selectors, clamp, helpers.
`).concat(ii({paths:n,minVisibilityThreshold:i,fullVisibilityThreshold:o}),`

void main() {
  int vIdx = int(a_vertexIndex);
  int pairIdx = vIdx / 2;
  int side = vIdx - pairIdx * 2; // 0 = left/bottom, 1 = right/top

  // --- Fetch edge data (2 texels per edge) ---
  int edgeIdx = int(a_edgeIndex);
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 e0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 e1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, e0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, e1, 0);

  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float thickness = edgeData0.z;
  int pathId = int(edgeData1.z);

  // --- Fetch path attributes (curvature, etc.) ---
  {
    int edgeIdx = int(a_edgeAttrIndex);
`).concat(c.fetchCode,`
`).concat(c.varyingAssignments,`
  }

  // --- Fetch node data: geometry (texel 0) + rotation flags (texel 1) ---
  vec4 srcN = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtN = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 source = srcN.xy;
  vec2 target = tgtN.xy;
  float sourceSize = srcN.z;
  float targetSize = tgtN.z;
  v_sourceNodeSize = sourceSize;
  v_targetNodeSize = targetSize;

  // --- Pixel-to-graph conversion (fixed font mode) ---
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float pixelToGraph = 2.0 / (matrixScaleX * u_resolution.x);

  float webGLThickness = thickness * u_correctionRatio / u_sizeRatio;

  // --- Body bounds (shared with edge label shader) ---
  vec4 edgeClamp = readFrameTexel(u_edgeFrameTexture, u_edgeFrameTextureWidth, edgeIdx);
  vec3 bodyBounds = computeEdgeLabelBodyBounds(
    edgeClamp.x, edgeClamp.y, edgeClamp.w,
    webGLThickness, HEAD_RATIO, TAIL_RATIO
  );
  float bodyStartDist = bodyBounds.x;
  float bodyEndDist = bodyBounds.y;
  float bodyLength = bodyBounds.z;

  // --- Text dimensions ---
  float baseFontSize = a_baseFontSize;
  `).concat(l?`float fontScale = baseFontSize / ATLAS_FONT_SIZE * u_zoomSizeRatio;
  float textWidthWebGL = a_totalTextWidth * fontScale * u_correctionRatio / u_sizeRatio;
  float halfTextHeight = baseFontSize * 0.35 * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;
  float marginWebGL = a_margin * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;`:`float fontScale = baseFontSize / ATLAS_FONT_SIZE;
  float textWidthWebGL = a_totalTextWidth * fontScale * pixelToGraph;
  float halfTextHeight = baseFontSize * 0.35 * pixelToGraph;
  float marginWebGL = a_margin * pixelToGraph;`,`
  float paddingWebGL = a_padding * pixelToGraph;

  // --- Alpha modifier (shared with edge label shader) ---
  float alphaModifier = computeEdgeLabelAlpha(bodyLength, textWidthWebGL);
  if (alphaModifier <= 0.0 || textWidthWebGL <= 0.0) {
    gl_Position = vec4(2.0, 0.0, 0.0, 1.0);
    v_color = vec4(0.0);
    v_id = vec4(0.0);
    v_alphaModifier = 0.0;
    return;
  }

  // --- Perpendicular offset (shared with edge label shader) ---
  float bodyCenterDist = (bodyStartDist + bodyEndDist) * 0.5;
  float centerT = queryPathTAtDistance(pathId, bodyCenterDist, source, target);
  float screenDir = computeEdgeLabelScreenDir(pathId, centerT, source, target, u_matrix);
  float readingSign = `).concat(s?"screenDir":"1.0",`;
  float halfThickness = webGLThickness * 0.5;
  float perpOffset = computeEdgeLabelPerpOffset(
    a_positionMode, halfThickness, marginWebGL, halfTextHeight, readingSign, screenDir
  );

  // --- Ribbon span (clipped to body) ---
  float halfTextWebGL = textWidthWebGL * 0.5;
  float labelStartDist = max(bodyCenterDist - halfTextWebGL, bodyStartDist);
  float labelEndDist = min(bodyCenterDist + halfTextWebGL, bodyEndDist);

  // Sample centerline at this pair, then apply perpendicular offset.
  // The ribbon follows the centerline path (simple & robust); for curved edges
  // this closely matches the offset path the characters sit on.
  float u = float(pairIdx) / float(RIBBON_SEGMENTS);
  float arcDist = mix(labelStartDist, labelEndDist, u);
  float t = queryPathTAtDistance(pathId, arcDist, source, target);
  vec2 pos = queryPathPosition(pathId, t, source, target);
  vec2 tan = queryPathTangent(pathId, t, source, target);
  vec2 perp = vec2(-tan.y, tan.x);

  vec2 centerPos = pos + perp * perpOffset;

  float halfRibbon = halfTextHeight + paddingWebGL;
  float sideSign = side == 0 ? -1.0 : 1.0;
  vec2 ribbonPos = centerPos + perp * (sideSign * halfRibbon);

  vec3 clipPos = u_matrix * vec3(ribbonPos, 1.0);
  gl_Position = vec4(clipPos.xy, 0.0, 1.0);

  v_color = a_color;
  v_id = a_id;
  v_alphaModifier = alphaModifier;
}
`);return f}var pu=`#version 300 es
precision highp float;

in vec4 v_color;
in vec4 v_id;
in float v_alphaModifier;

out vec4 fragColor;

void main() {
#ifdef PICKING_MODE
  if (v_alphaModifier <= 0.0) discard;
  fragColor = v_id;
#else
  float alpha = v_color.a * v_alphaModifier;
  if (alpha <= 0.0) discard;
  fragColor = vec4(v_color.rgb * alpha, alpha);
#endif
}
`;function mu(a,n,t,e){var r=e.shaderConfig,i=r.paths,o=r.fontSizeMode;if(i.length===0)throw new Error("createEdgeLabelBackgroundProgram: shaderConfig must declare at least one path");var s=Te(),l=me([].concat($(i),[s])),u=En([].concat($(i),[s]),l),d=vu(r),c=function(f){function h(g,m,p){var v;return Y(this,h),v=te(this,h,[g,m,p]),S(v,"totalCount",0),S(v,"bufferCapacity",0),S(v,"edgeAttributeTexture",null),v.edgeAttributeTexture=new Sn(g,l),v.packedAttributeData=new Float32Array(l.floatsPerItem),v}return ne(h,f),K(h,[{key:"getDefinition",value:function(){for(var m=WebGL2RenderingContext,p=m.FLOAT,v=m.UNSIGNED_BYTE,b=m.TRIANGLE_STRIP,y=[],T=0;T<Wr;T++)y.push([T]);var x=["u_matrix","u_sizeRatio","u_correctionRatio","u_pixelRatio","u_cameraAngle","u_resolution","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeFrameTexture","u_edgeFrameTextureWidth"];return o==="scaled"&&x.push("u_zoomSizeRatio"),l.floatsPerItem>0&&x.push("u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"),{VERTICES:Wr,VERTEX_SHADER_SOURCE:d,FRAGMENT_SHADER_SOURCE:pu,METHOD:b,UNIFORMS:x,ATTRIBUTES:[{name:"a_edgeIndex",size:1,type:p},{name:"a_edgeAttrIndex",size:1,type:p},{name:"a_baseFontSize",size:1,type:p},{name:"a_totalTextWidth",size:1,type:p},{name:"a_positionMode",size:1,type:p},{name:"a_margin",size:1,type:p},{name:"a_padding",size:1,type:p},{name:"a_color",size:4,type:v,normalized:!0},{name:"a_id",size:4,type:v,normalized:!0}],CONSTANT_ATTRIBUTES:[{name:"a_vertexIndex",size:1,type:p}],CONSTANT_DATA:y}}},{key:"processEdgeLabelBackground",value:function(m,p,v){var b=0;if(this.edgeAttributeTexture&&l.floatsPerItem>0){b=this.edgeAttributeTexture.allocate(p);var y=this.packedAttributeData;Rn(u,v.edgeAttributes,y,"",gu,0),this.edgeAttributeTexture.updateAllAttributes(p,y)}var T=this.floats,x=this.ints,_=m*this.STRIDE;T[_++]=v.edgeIndex,T[_++]=b,T[_++]=v.baseFontSize,T[_++]=v.totalTextWidth,T[_++]=v.positionMode,T[_++]=v.margin,T[_++]=v.padding,T[_++]=v.color,x[_++]=v.id}},{key:"setUniforms",value:function(m,p){var v=p.gl,b=p.uniformLocations;if(v.uniformMatrix3fv(b.u_matrix,!1,m.matrix),v.uniform1f(b.u_sizeRatio,m.sizeRatio),v.uniform1f(b.u_correctionRatio,m.correctionRatio),v.uniform1f(b.u_pixelRatio,m.pixelRatio),v.uniform1f(b.u_cameraAngle,m.cameraAngle),v.uniform2f(b.u_resolution,m.width,m.height),b.u_nodeDataTexture!==void 0&&v.uniform1i(b.u_nodeDataTexture,m.nodeDataTextureUnit),b.u_nodeDataTextureWidth!==void 0&&v.uniform1i(b.u_nodeDataTextureWidth,m.nodeDataTextureWidth),b.u_edgeDataTexture!==void 0&&v.uniform1i(b.u_edgeDataTexture,m.edgeDataTextureUnit),b.u_edgeDataTextureWidth!==void 0&&v.uniform1i(b.u_edgeDataTextureWidth,m.edgeDataTextureWidth),b.u_edgeFrameTexture!==void 0&&v.uniform1i(b.u_edgeFrameTexture,m.edgeFrameTextureUnit),b.u_edgeFrameTextureWidth!==void 0&&v.uniform1i(b.u_edgeFrameTextureWidth,m.edgeFrameTextureWidth),o==="scaled"&&b.u_zoomSizeRatio!==void 0){var y=this.renderer.getSetting("zoomToSizeRatioFunction");v.uniform1f(b.u_zoomSizeRatio,1/y(m.zoomRatio))}this.edgeAttributeTexture&&l.floatsPerItem>0&&b.u_edgeAttributeTexture!==void 0&&(this.edgeAttributeTexture.bind(Ne),v.uniform1i(b.u_edgeAttributeTexture,Ne),v.uniform1i(b.u_edgeAttributeTextureWidth,this.edgeAttributeTexture.getTextureWidth()),v.uniform1i(b.u_edgeAttributeTexelsPerEdge,this.edgeAttributeTexture.getTexelsPerItem()))}},{key:"renderProgram",value:function(m,p){this.edgeAttributeTexture&&l.floatsPerItem>0&&this.edgeAttributeTexture.upload(),ie(h,"renderProgram",this,3)([m,p])}},{key:"kill",value:function(){this.edgeAttributeTexture&&(this.edgeAttributeTexture.kill(),this.edgeAttributeTexture=null),ie(h,"kill",this,3)([])}},{key:"drawWebGL",value:function(m,p){var v=p.gl;this.totalCount!==0&&v.drawArraysInstanced(v.TRIANGLE_STRIP,0,this.VERTICES,this.totalCount)}},{key:"reallocate",value:function(m){this.totalCount=m,m>this.bufferCapacity&&(this.bufferCapacity=Math.max(m,Math.ceil(this.bufferCapacity*1.5)||10),ie(h,"reallocate",this,3)([this.bufferCapacity]))}}])}(He);return new c(a,n,t)}function si(a){var n,t,e,r,i,o;return{paths:a.paths,headLengthRatio:(n=a.headLengthRatio)!==null&&n!==void 0?n:0,tailLengthRatio:(t=a.tailLengthRatio)!==null&&t!==void 0?t:0,fontSizeMode:(e=a.fontSizeMode)!==null&&e!==void 0?e:"fixed",minVisibilityThreshold:(r=a.minVisibilityThreshold)!==null&&r!==void 0?r:.7,fullVisibilityThreshold:(i=a.fullVisibilityThreshold)!==null&&i!==void 0?i:.8,keepUpright:(o=a.keepUpright)!==null&&o!==void 0?o:!0}}var bu=Se.fontSize,yu=17/64;function xu(a){var n=a.paths,t=a.hasBorder,e=t===void 0?!1:t,r=a.fontSizeMode,i=r===void 0?"fixed":r,o=a.minVisibilityThreshold,s=o===void 0?.5:o,l=a.fullVisibilityThreshold,u=l===void 0?.6:l,d=a.keepUpright,c=d===void 0?!0:d,f=i==="scaled",h=n.some(function(b){return b.hasSharpCorners}),g=Te(),m=me([].concat($(n),[g])),p=Nt(m),v=`#version 300 es

// ============================================================================
// Attributes - Per Character (Instanced)
// ============================================================================

// Edge geometry: indices for texture lookup
// Edge data (source/target node indices, thickness, head/tail ratios) is fetched from edge data texture
// Edge path attributes (curvature, etc.) are fetched from edge attribute texture
in float a_edgeIndex;       // Index into edge data texture
in float a_edgeAttrIndex;   // Index into edge attribute texture (for curvature, etc.)
in float a_baseFontSize;    // Base font size in pixels (per-label)

// Character metrics (in glyph units = atlas font size pixels)
in vec4 a_charMetrics;      // (charTextOffset, charAdvance, totalTextWidth, positionMode)
in vec4 a_charDims;         // (charSize.x, charSize.y, charOffset.x, charOffset.y)

// Atlas texture coordinates
in vec4 a_texCoords;        // (x, y, width, height) in atlas pixels

// Label parameters
in vec2 a_labelParams;      // (margin, unused)

// Appearance
in vec4 a_color;            // Character color (RGBA, normalized)
`.concat(e?"in vec4 a_borderColor;      // Border color (RGBA, normalized)":"",`

// ============================================================================
// Attributes - Per Vertex (Constant)
// ============================================================================

in vec2 a_quadCorner;       // Quad corner: (0,0), (1,0), (0,1), (1,1)

// ============================================================================
// Uniforms
// ============================================================================

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_correctionRatio;
uniform float u_pixelRatio;
uniform float u_cameraAngle;    // Required by node shape SDFs
// u_sdfBufferPixels kept for ABI compatibility but unused in shader
uniform float u_sdfBufferPixels;
uniform vec2 u_resolution;
uniform vec2 u_atlasSize;
uniform sampler2D u_nodeDataTexture; // Shared texture with node position/size/shape data
uniform int u_nodeDataTextureWidth;  // Width of 2D node data texture for coordinate calculation
uniform sampler2D u_edgeDataTexture; // Shared texture with edge data
uniform int u_edgeDataTextureWidth;  // Width of 2D edge data texture for coordinate calculation
uniform sampler2D u_edgeFrameTexture; // Per-edge clamp (tStart, tEnd, straightenFactor, pathLength)
uniform int u_edgeFrameTextureWidth;
`).concat(f?"uniform float u_zoomSizeRatio;  // Zoom-based size ratio from zoomToSizeRatioFunction":"",`

// Edge path attribute texture uniforms (for curvature and other path attributes)
`).concat(p.uniformDeclarations,`

// ============================================================================
// Varyings
// ============================================================================

out vec2 v_texCoord;
out vec4 v_color;
`).concat(e?"out vec4 v_borderColor;":"",`
out float v_edgeFade;  // 0 = fully visible, 1 = fully faded (outside body)
out float v_alphaModifier;  // 0-1 based on label visibility ratio
out float v_fontScale;  // Ratio of rendered font size to atlas font size
`).concat(e?"out float v_positionMode;  // Position mode for conditional border (0=over needs border)":"",`

// ============================================================================
// Constants
// ============================================================================

const float bias = 255.0 / 254.0;
const float FADE_WIDTH_PIXELS = 15.0;  // Width of fade gradient in pixels
const float ATLAS_FONT_SIZE = `).concat(ae(bu),`;  // Base font size used in SDF atlas
const float VERTICAL_CENTER_RATIO = `).concat(ae(yu),`;  // Baseline to visual center ratio

// ============================================================================
// Path Attribute Variables (set in main, used by path functions)
// ============================================================================
// Path attributes are fetched from the edge attribute texture and stored in
// variables with v_ prefix (e.g., v_curvature) for path functions to access.
`).concat(p.vertexVaryingDeclarations.replace(/out /g,""),`

// Node size variables (set in main, used by some path functions like loops).
// These mirror the v_sourceNodeSize / v_targetNodeSize varyings in generator.ts,
// but are plain floats here since the label shader is vertex-only.
float v_sourceNodeSize;
float v_targetNodeSize;

// Shared preamble: shape SDFs, path functions + selectors, clamp, helpers.
`).concat(ii({paths:n,minVisibilityThreshold:s,fullVisibilityThreshold:u}),`

// ============================================================================
// Main
// ============================================================================

void main() {
  // -------------------------------------------------------------------------
  // Fetch edge data from edge texture (2 texels per edge)
  // -------------------------------------------------------------------------
  // Texel 0: sourceNodeIndex, targetNodeIndex, thickness, reserved
  // Texel 1: headLengthRatio, tailLengthRatio, pathId, extremityIds
  int edgeIdx = int(a_edgeIndex);
  int texel0Idx = edgeIdx * 2;
  int texel1Idx = edgeIdx * 2 + 1;
  ivec2 edgeTexCoord0 = ivec2(texel0Idx % u_edgeDataTextureWidth, texel0Idx / u_edgeDataTextureWidth);
  ivec2 edgeTexCoord1 = ivec2(texel1Idx % u_edgeDataTextureWidth, texel1Idx / u_edgeDataTextureWidth);
  vec4 edgeData0 = texelFetch(u_edgeDataTexture, edgeTexCoord0, 0);
  vec4 edgeData1 = texelFetch(u_edgeDataTexture, edgeTexCoord1, 0);

  // Unpack edge data
  int srcIdx = int(edgeData0.x);
  int tgtIdx = int(edgeData0.y);
  float thickness = edgeData0.z;
  // edgeData0.w is reserved
  float headLengthRatio = edgeData1.x;
  float tailLengthRatio = edgeData1.y;
  int pathId = int(edgeData1.z);  // Path type for multi-path support
  float baseFontSize = a_baseFontSize;

  // -------------------------------------------------------------------------
  // Fetch path attributes from edge attribute texture
  // -------------------------------------------------------------------------
  // Note: The fetch code uses 'edgeIdx' variable, so we set it to the attribute texture index
  {
    int edgeIdx = int(a_edgeAttrIndex);  // Use attribute texture index for path attributes
`).concat(p.fetchCode,`
`).concat(p.varyingAssignments,`
  }

  // -------------------------------------------------------------------------
  // Fetch node data from node texture (geometry texel + rotation-flags texel)
  // -------------------------------------------------------------------------
  vec4 srcNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, srcIdx);
  vec4 tgtNodeData = readNodeData(u_nodeDataTexture, u_nodeDataTextureWidth, tgtIdx);

  vec2 source = srcNodeData.xy;
  vec2 target = tgtNodeData.xy;
  float sourceSize = srcNodeData.z;
  float targetSize = tgtNodeData.z;
  v_sourceNodeSize = sourceSize;
  v_targetNodeSize = targetSize;
  float charTextOffset = a_charMetrics.x;
  float charAdvance = a_charMetrics.y;
  float totalTextWidth = a_charMetrics.z;
  float positionMode = a_charMetrics.w;
  vec2 charSize = a_charDims.xy;
  vec2 charOffset = a_charDims.zw;
  float margin = a_labelParams.x;

  // -------------------------------------------------------------------------
  // Compute pixel-to-graph conversion (for fixed font size mode)
  // -------------------------------------------------------------------------
  // This converts screen pixels to graph units such that N pixels on screen
  // becomes N pixels regardless of zoom level.
  // matrixScaleX is how much the matrix scales graph units to clip space
  float matrixScaleX = length(vec2(u_matrix[0][0], u_matrix[1][0]));
  float pixelToGraph = 2.0 / (matrixScaleX * u_resolution.x);

  // -------------------------------------------------------------------------
  // Step 1: Convert thickness to WebGL units
  // -------------------------------------------------------------------------
  float webGLThickness = thickness * u_correctionRatio / u_sizeRatio;

  // -------------------------------------------------------------------------
  // Step 2: Compute body bounds (truncated at node boundaries + extremities)
  // -------------------------------------------------------------------------
  vec4 edgeClamp = readFrameTexel(u_edgeFrameTexture, u_edgeFrameTextureWidth, edgeIdx);
  vec3 bodyBounds = computeEdgeLabelBodyBounds(
    edgeClamp.x, edgeClamp.y, edgeClamp.w,
    webGLThickness, headLengthRatio, tailLengthRatio
  );
  float bodyStartDist = bodyBounds.x;
  float bodyEndDist = bodyBounds.y;
  float bodyLength = bodyBounds.z;

  // -------------------------------------------------------------------------
  // Step 3: Compute font scale and text dimensions
  // -------------------------------------------------------------------------
  // Font size modes:
  // - "fixed": Constant pixel size regardless of zoom, using pixelToGraph conversion
  // - "scaled": Scales with zoom using zoomToSizeRatioFunction
  `).concat(f?`// Scaled mode: font scales with zoom
  float fontScale = baseFontSize / ATLAS_FONT_SIZE * u_zoomSizeRatio;
  // Convert glyph-unit metrics to WebGL units (scales with zoom)
  float textWidthWebGL = totalTextWidth * fontScale * u_correctionRatio / u_sizeRatio;
  float charOffsetWebGL = charTextOffset * fontScale * u_correctionRatio / u_sizeRatio;
  float charAdvanceWebGL = charAdvance * fontScale * u_correctionRatio / u_sizeRatio;`:`// Fixed mode: font stays constant in screen pixels
  float fontScale = baseFontSize / ATLAS_FONT_SIZE;
  // Convert glyph-unit metrics to graph units using pixelToGraph (zoom-independent)
  float textWidthWebGL = totalTextWidth * fontScale * pixelToGraph;
  float charOffsetWebGL = charTextOffset * fontScale * pixelToGraph;
  float charAdvanceWebGL = charAdvance * fontScale * pixelToGraph;`,`

  // Font scale varying for fragment shader gamma scaling.
  // Ratio of rendered font size to atlas font size \u2014 used to tighten the
  // anti-aliasing band for large labels so they stay sharp.
  v_fontScale = fontScale;

  // -------------------------------------------------------------------------
  // Step 4: Alpha modifier from how much of the label fits in the body
  // -------------------------------------------------------------------------
  float alphaModifier = computeEdgeLabelAlpha(bodyLength, textWidthWebGL);

  // -------------------------------------------------------------------------
  // Step 5: Compute character center offset (truncation check moved to after curvature adjustment)
  // -------------------------------------------------------------------------
  // Body center in arc distance
  float bodyCenterDist = (bodyStartDist + bodyEndDist) * 0.5;

  float centerT = queryPathTAtDistance(pathId, bodyCenterDist, source, target);
  float screenDir = computeEdgeLabelScreenDir(pathId, centerT, source, target, u_matrix);

  // Reversed labels lay their characters out from target to source
  float readingSign = `).concat(c?"screenDir":"1.0",`;

  // Character center position relative to label center (on centerline, before curvature adjustment)
  float charCenterOffset = readingSign * (charOffsetWebGL + charAdvanceWebGL * 0.5 - textWidthWebGL * 0.5);

  // -------------------------------------------------------------------------
  // Step 6: Compute perpendicular offset based on position mode
  // -------------------------------------------------------------------------
  // Position modes: 0=over, 1=above, 2=below, 3=auto
  // Needed early for curvature-adaptive character spacing in Step 7
  float halfThickness = webGLThickness * 0.5;
  `).concat(f?`// Scaled mode: margin and text height scale with zoom (same factor as font)
  float marginWebGL = margin * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;
  float halfTextHeight = baseFontSize * 0.35 * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;`:`// Fixed mode: margin and text height stay constant in screen pixels
  float marginWebGL = margin * pixelToGraph;
  float halfTextHeight = baseFontSize * 0.35 * pixelToGraph;`,`
  float perpOffset = computeEdgeLabelPerpOffset(
    positionMode, halfThickness, marginWebGL, halfTextHeight, readingSign, screenDir
  );

  // -------------------------------------------------------------------------
  // Step 7: Position character on path using offset path traversal
  // -------------------------------------------------------------------------
  // For "over" mode (perpOffset = 0), use simple centerline placement
  // For above/below modes, walk along the offset path to find correct position
  float charT;

  if (perpOffset == 0.0) {
    // Simple case: place on centerline
    float charArcDist = bodyCenterDist + charCenterOffset;
    charT = queryPathTAtDistance(pathId, charArcDist, source, target);
  } else {
    // Offset path traversal: walk along the offset curve to find character position
    // This ensures even character spacing regardless of curvature

    `).concat(h?`// -----------------------------------------------------------------------
    // Corner skip setup for step/taxi edges with above/below labels
    // -----------------------------------------------------------------------
    // At concave corners (inner side of the bend), characters would bunch up
    // because the offset path has near-zero arc length. We detect corner
    // crossings during the offset path traversal and add skip distance.

    // Get corner t values and concavity
    vec2 cornerTs = queryGetCornerTs(pathId, source, target);
    vec2 concavity = queryGetCornerConcavity(pathId, source, target, perpOffset);

    // Skip distance in graph units, proportional to on-screen font size
    // For fixed mode: use pixelToGraph so gap stays constant regardless of zoom
    // For scaled mode: use the same conversion as text width
    `.concat(f?"float skipDistGraph = STEP_INNER_CORNER_SKIP_FACTOR * baseFontSize * u_zoomSizeRatio * u_correctionRatio / u_sizeRatio;":"float skipDistGraph = STEP_INNER_CORNER_SKIP_FACTOR * baseFontSize * pixelToGraph;",`

    // Corner t values for detecting crossings during traversal
    float corner1T = cornerTs.x;
    float corner2T = cornerTs.y;
    bool corner1IsConcave = concavity.x > 0.5;
    bool corner2IsConcave = concavity.y > 0.5;`):"",`

    // Target distance along offset path from center
    float targetOffsetDist = abs(charCenterOffset);

    // Handle center character (charCenterOffset \u2248 0) - no search needed
    if (targetOffsetDist < 0.0001) {
      charT = centerT;
    } else {
      vec2 centerPos = queryPathPosition(pathId, centerT, source, target);
      vec2 centerNormal = queryPathNormal(pathId, centerT, source, target);
      vec2 offsetCenter = centerPos + centerNormal * perpOffset;

      float searchDir = charCenterOffset > 0.0 ? 1.0 : -1.0;

      // Search bounds (t values for body start and end)
      float tBodyStart = queryPathTAtDistance(pathId, bodyStartDist, source, target);
      float tBodyEnd = queryPathTAtDistance(pathId, bodyEndDist, source, target);

      // Walk along offset path to find character position
      float accumDist = 0.0;
      vec2 prevOffsetPos = offsetCenter;
      float prevT = centerT;
      float foundT = centerT;

      // Search range depends on direction
      float tSearchEnd = searchDir > 0.0 ? tBodyEnd : tBodyStart;

      `).concat(h?`// Track which concave corners we've crossed to add skip distance
      bool crossedCorner1 = false;
      bool crossedCorner2 = false;
      float effectiveTargetDist = targetOffsetDist;`:"",`

      const int STEPS = 32;
      for (int i = 1; i <= STEPS; i++) {
        // Step along centerline t, from center toward target
        float stepT = centerT + searchDir * float(i) * abs(tSearchEnd - centerT) / float(STEPS);

        `).concat(h?`// Check for concave corner crossings and add skip distance
        // Corner 1 crossing check
        if (corner1IsConcave && !crossedCorner1) {
          bool crossingCorner1 = (searchDir > 0.0)
            ? (prevT < corner1T && stepT >= corner1T)
            : (prevT > corner1T && stepT <= corner1T);
          if (crossingCorner1) {
            crossedCorner1 = true;
            effectiveTargetDist += skipDistGraph;
          }
        }

        // Corner 2 crossing check
        if (corner2IsConcave && !crossedCorner2) {
          bool crossingCorner2 = (searchDir > 0.0)
            ? (prevT < corner2T && stepT >= corner2T)
            : (prevT > corner2T && stepT <= corner2T);
          if (crossingCorner2) {
            crossedCorner2 = true;
            effectiveTargetDist += skipDistGraph;
          }
        }`:"",`

        // Compute offset position at this t
        vec2 stepPos = queryPathPosition(pathId, stepT, source, target);
        vec2 stepNormal = queryPathNormal(pathId, stepT, source, target);
        vec2 offsetPos = stepPos + stepNormal * perpOffset;

        // Distance along offset path
        float segDist = length(offsetPos - prevOffsetPos);

        `).concat(h?`if (accumDist + segDist >= effectiveTargetDist) {
          // Interpolate within segment to find exact t
          float remaining = effectiveTargetDist - accumDist;
          float segT = remaining / max(segDist, 0.0001);
          foundT = mix(prevT, stepT, segT);
          break;
        }`:`if (accumDist + segDist >= targetOffsetDist) {
          // Interpolate within segment to find exact t
          float remaining = targetOffsetDist - accumDist;
          float segT = remaining / max(segDist, 0.0001);
          foundT = mix(prevT, stepT, segT);
          break;
        }`,`

        accumDist += segDist;
        prevOffsetPos = offsetPos;
        prevT = stepT;
        // Update foundT to last valid position in case loop exhausts without finding target
        foundT = stepT;
      }

      charT = foundT;
    }
  }

  // Get position and tangent at final character position
  vec2 pathPos = queryPathPosition(pathId, charT, source, target);
  vec2 tangent = queryPathTangent(pathId, charT, source, target);

  // Compute perpendicular direction (90 degrees from tangent)
  vec2 perpDir = vec2(-tangent.y, tangent.x);

  // Apply perpendicular offset to path position
  vec2 offsetPathPos = pathPos + perpDir * perpOffset;

  // -------------------------------------------------------------------------
  // Step 8: Build character quad
  // -------------------------------------------------------------------------
  // Character size in screen pixels
  vec2 charSizePixels = charSize * fontScale;

  // Character offset from origin to the atlas region's top-left corner.
  // bearingX/bearingY already include the SDF buffer.
  vec2 charOffsetPixels = charOffset * fontScale;

  // The character's local X offset from pathPos (which is at character center)
  float charLocalX = -charAdvance * 0.5 * fontScale;

  // Build quad position:
  // - Start at character origin (charLocalX on X axis, 0 on Y axis = baseline)
  // - Add bearing offset to get to atlas region corner
  // - Add quad corner * size to get vertex position
  vec2 quadPos;
  quadPos.x = charLocalX + charOffsetPixels.x + a_quadCorner.x * charSizePixels.x;
  // charOffset.y = -bearingY (negated), so -charOffsetPixels.y = bearingY * fontScale
  // (distance from baseline to atlas region top, positive = upward)
  // Quad corner (0,0) = bottom-left, (1,1) = top-right
  quadPos.y = -charOffsetPixels.y - charSizePixels.y * (1.0 - a_quadCorner.y);

  // Center vertically on the path by offsetting by half the visual text height
  // VERTICAL_CENTER_RATIO is the distance from baseline to visual center as a ratio of atlas font size
  float verticalCenterOffset = VERTICAL_CENTER_RATIO * ATLAS_FONT_SIZE * fontScale;
  quadPos.y -= verticalCenterOffset;

  // -------------------------------------------------------------------------
  // Step 9: Rotate quad to align with tangent
  // -------------------------------------------------------------------------
  // Rotation matrix from the reading direction
  // readingDir = (cos(angle), sin(angle)), so we can build rotation directly
  vec2 readingDir = tangent * readingSign;
  mat2 rotation = mat2(readingDir.x, readingDir.y, -readingDir.y, readingDir.x);

  // Convert pixel offset to WebGL units for rotation
  `).concat(f?"vec2 quadPosWebGL = quadPos * u_correctionRatio / u_sizeRatio; // Scaled mode":"vec2 quadPosWebGL = quadPos * pixelToGraph; // Fixed mode: use pixelToGraph for zoom-independent size",`

  // Rotate around character center on path
  vec2 rotatedOffset = rotation * quadPosWebGL;

  // Final position in graph space (using offset path position for above/below modes)
  vec2 worldPos = offsetPathPos + rotatedOffset;

  // -------------------------------------------------------------------------
  // Step 10: Transform to clip space
  // -------------------------------------------------------------------------
  vec3 clipPos = u_matrix * vec3(worldPos, 1.0);
  gl_Position = vec4(clipPos.xy, 0.0, 1.0);

  // -------------------------------------------------------------------------
  // Step 11: Texture coordinates
  // -------------------------------------------------------------------------
  // Flip Y for texture coordinates (texture Y goes down, quad Y goes up)
  vec2 texCorner = vec2(a_quadCorner.x, 1.0 - a_quadCorner.y);
  v_texCoord = (a_texCoords.xy + texCorner * a_texCoords.zw) / u_atlasSize;

  // -------------------------------------------------------------------------
  // Step 12: Pass color, border color, and alpha modifier
  // -------------------------------------------------------------------------
  v_color = a_color;
  v_color.a *= bias;
`).concat(e?`  v_borderColor = a_borderColor;
  v_borderColor.a *= bias;
  v_positionMode = positionMode;`:"",`
  v_alphaModifier = alphaModifier;

  // -------------------------------------------------------------------------
  // Step 13: Compute edge fade for soft truncation
  // -------------------------------------------------------------------------
  // Convert fade width from pixels to WebGL units
  `).concat(f?"float fadeWidthWebGL = FADE_WIDTH_PIXELS * u_correctionRatio / u_sizeRatio;":"float fadeWidthWebGL = FADE_WIDTH_PIXELS * pixelToGraph;",`

  // Compute the arc position of THIS VERTEX (not just character center)
  // The quad extends from charCenter - advance/2 to charCenter + advance/2
  // a_quadCorner.x is 0 for left edge, 1 for right edge
  float vertexLocalOffset = readingSign * (a_quadCorner.x - 0.5) * charAdvanceWebGL;
  float vertexArcOffset = charCenterOffset + vertexLocalOffset;

  // Compute distance from body edges (positive = inside body, negative = outside)
  float halfBody = bodyLength * 0.5;
  float distFromStart = vertexArcOffset + halfBody;  // Distance from body start edge
  float distFromEnd = halfBody - vertexArcOffset;    // Distance from body end edge
  float distFromEdge = min(distFromStart, distFromEnd);

  // Compute fade: 0 = fully visible (deep inside body), 1 = fully faded (at body edge)
  // Fade goes from 0 (at 2*fadeWidth inside) to 1 (at body edge)
  // This ensures text is fully transparent before reaching extremities
  v_edgeFade = 1.0 - smoothstep(0.0, fadeWidthWebGL * 2.0, distFromEdge);
}
`);return v}function _u(){var a=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},n=a.hasBorder,t=n===void 0?!1:n,e=`#version 300 es
precision highp float;

in vec2 v_texCoord;
in vec4 v_color;
`.concat(t?"in vec4 v_borderColor;":"",`
in float v_edgeFade;  // 0 = fully visible, 1 = fully faded
in float v_alphaModifier;  // 0-1 based on label visibility ratio
in float v_fontScale;  // Ratio of rendered font size to atlas font size
`).concat(t?"in float v_positionMode;  // Position mode (0=over, 1=above, 2=below, 3=auto)":"",`

uniform sampler2D u_atlas;
uniform float u_gamma;
uniform float u_sdfBuffer;
uniform float u_pixelRatio;
`).concat(t?"uniform float u_borderWidth;  // Border width in SDF units (normalized)":"",`

// Fragment output (single target - picking handled via separate pass)
out vec4 fragColor;

void main() {
  #ifdef PICKING_MODE
    // Edge labels are not pickable - discard all fragments in picking mode
    fragColor = vec4(0.0);
    discard;
  #else
  // SDF stores normalized distance: 0.5 = on edge, >0.5 = inside glyph
  float sdfValue = texture(u_atlas, v_texCoord).a;

  // Edge threshold accounting for SDF buffer padding
  float edge = 1.0 - u_sdfBuffer;

  // Scale gamma inversely with font scale so small labels get a wider AA band
  // (smoother) and large labels get a tighter band (sharper).
  float aaWidth = u_gamma / (u_pixelRatio * v_fontScale);

  // Apply edge fade for soft truncation at body boundaries
  // Also apply visibility-based alpha modifier for short edge labels
  float edgeAlpha = (1.0 - v_edgeFade) * v_alphaModifier;

`).concat(t?`  // Fill alpha: fully opaque inside the glyph
  float fillAlpha = smoothstep(edge - aaWidth, edge + aaWidth, sdfValue);

  // Only apply border for "over" position mode (v_positionMode == 0.0)
  // Labels positioned above/below/auto don't overlap the edge line and don't need borders
  if (v_positionMode < 0.5) {
    // Border rendering: compute alpha for both fill and border regions
    // Border extends from (edge - borderWidth) to edge
    float borderEdge = edge - u_borderWidth;

    // Border alpha: opaque in the border region (between borderEdge and edge)
    float borderAlpha = smoothstep(borderEdge - aaWidth, borderEdge + aaWidth, sdfValue);

    // Composite: fill on top of border
    // Border is visible where borderAlpha > 0 but fillAlpha < 1
    vec3 borderColorPremult = v_borderColor.rgb * v_borderColor.a * borderAlpha * edgeAlpha;
    vec3 fillColorPremult = v_color.rgb * v_color.a * fillAlpha * edgeAlpha;

    // Blend fill over border (fill replaces border where fill is opaque)
    float finalBorderAlpha = borderAlpha * (1.0 - fillAlpha);
    vec3 finalColor = fillColorPremult + v_borderColor.rgb * v_borderColor.a * finalBorderAlpha * edgeAlpha;
    float finalAlpha = (v_color.a * fillAlpha + v_borderColor.a * finalBorderAlpha) * edgeAlpha;

    fragColor = vec4(finalColor, finalAlpha);
  } else {
    // No border for above/below/auto positions - simple text rendering
    float finalAlpha = v_color.a * fillAlpha * edgeAlpha;
    fragColor = vec4(v_color.rgb * finalAlpha, finalAlpha);
  }`:`  // Smooth transition from transparent to opaque at glyph edge
  float alpha = smoothstep(edge - aaWidth, edge + aaWidth, sdfValue);

  // Premultiplied alpha output
  float finalAlpha = v_color.a * alpha * edgeAlpha;
  fragColor = vec4(v_color.rgb * finalAlpha, finalAlpha);`,`
  #endif
}
`);return e}function Tu(a){var n=arguments.length>1&&arguments[1]!==void 0?arguments[1]:!1,t=arguments.length>2&&arguments[2]!==void 0?arguments[2]:"fixed",e=["u_matrix","u_sizeRatio","u_correctionRatio","u_pixelRatio","u_cameraAngle","u_sdfBufferPixels","u_resolution","u_atlasSize","u_atlas","u_gamma","u_sdfBuffer","u_nodeDataTexture","u_nodeDataTextureWidth","u_edgeDataTexture","u_edgeDataTextureWidth","u_edgeFrameTexture","u_edgeFrameTextureWidth","u_edgeAttributeTexture","u_edgeAttributeTextureWidth","u_edgeAttributeTexelsPerEdge"];t==="scaled"&&e.push("u_zoomSizeRatio"),n&&e.push("u_borderWidth");var r=M(a),i;try{for(r.s();!(i=r.n()).done;){var o=i.value,s=M(o.uniforms),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;e.includes(u.name)||e.push(u.name)}}catch(d){s.e(d)}finally{s.f()}}}catch(d){r.e(d)}finally{r.f()}return e}function Su(a){var n=a.hasBorder,t=n===void 0?!1:n,e=a.fontSizeMode,r=e===void 0?"fixed":e;return{vertexShader:xu(a),fragmentShader:_u({hasBorder:t}),uniforms:Tu(a.paths,t,r)}}var Eu=new Map;function Ru(a){switch(a){case"over":return 0;case"above":return 1;case"below":return 2;case"auto":return 3;default:return 0}}function Au(a,n,t,e){var r=e.color,i=e.margin,o=e.textBorder,s=si(e),l=s.paths,u=s.fontSizeMode,d=s.minVisibilityThreshold,c=s.fullVisibilityThreshold,f=s.keepUpright,h=!!o,g=Su({paths:l,hasBorder:h,fontSizeMode:u,minVisibilityThreshold:d,fullVisibilityThreshold:c,keepUpright:f}),m=function(p){function v(b,y,T){var x;Y(this,v),x=te(this,v,[b,y,T]),S(x,"atlasTexture",null),S(x,"atlasNeedsUpdate",!1),S(x,"refreshTimeout",null),S(x,"labelGlyphCache",new Map),S(x,"edgeAttributeTexture",null);var _=Te();if(x.attributeLayout=me([].concat($(l),[_])),x.attrDescriptors=En([].concat($(l),[_]),x.attributeLayout),x.edgeAttributeTexture=new Sn(b,x.attributeLayout),x.packedAttributeData=new Float32Array(x.attributeLayout.floatsPerItem),x.atlasManager=new Oe,x.gamma=.025,x.sdfBuffer=Se.cutoff,x.atlasTexture=b.createTexture(),!x.atlasTexture)throw new Error("EdgeLabelProgram: failed to create atlas texture");b.bindTexture(b.TEXTURE_2D,x.atlasTexture),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_WRAP_S,b.CLAMP_TO_EDGE),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_WRAP_T,b.CLAMP_TO_EDGE),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_MIN_FILTER,b.LINEAR),b.texParameteri(b.TEXTURE_2D,b.TEXTURE_MAG_FILTER,b.LINEAR),b.bindTexture(b.TEXTURE_2D,null),x.atlasManager.on(Oe.ATLAS_UPDATED_EVENT,function(){x.atlasNeedsUpdate=!0,x.refreshTimeout!==null&&clearTimeout(x.refreshTimeout),x.refreshTimeout=setTimeout(function(){x.refreshTimeout=null,x.renderer.refresh()},0)});var R={family:"sans-serif",weight:"normal",style:"normal"};return x.defaultFontKey=x.atlasManager.registerFont(R),x}return ne(v,p),K(v,[{key:"getDefinition",value:function(){var y=WebGL2RenderingContext,T=y.FLOAT,x=y.UNSIGNED_BYTE,_=y.TRIANGLE_STRIP,R=new Set,E=[],L=M(l),D;try{for(L.s();!(D=L.n()).done;){var F=D.value,A=M(F.attributes),I;try{for(A.s();!(I=A.n()).done;){var w=I.value,k=w.name.startsWith("a_")?w.name:"a_".concat(w.name);R.has(k)||(R.add(k),E.push({name:k,size:w.size,type:w.type}))}}catch(G){A.e(G)}finally{A.f()}}}catch(G){L.e(G)}finally{L.f()}return{VERTICES:4,VERTEX_SHADER_SOURCE:g.vertexShader,FRAGMENT_SHADER_SOURCE:g.fragmentShader,METHOD:_,UNIFORMS:g.uniforms,ATTRIBUTES:[{name:"a_edgeIndex",size:1,type:T},{name:"a_edgeAttrIndex",size:1,type:T},{name:"a_baseFontSize",size:1,type:T},{name:"a_charMetrics",size:4,type:T},{name:"a_charDims",size:4,type:T},{name:"a_texCoords",size:4,type:T},{name:"a_labelParams",size:2,type:T},{name:"a_color",size:4,type:x,normalized:!0}].concat($(h?[{name:"a_borderColor",size:4,type:x,normalized:!0}]:[]),$(E.filter(function(G){return!["a_curvature","curvature"].includes(G.name)}))),CONSTANT_ATTRIBUTES:[{name:"a_quadCorner",size:2,type:T}],CONSTANT_DATA:[[0,0],[1,0],[0,1],[1,1]]}}},{key:"prepareLabelGlyphs",value:function(y,T){if(T.hidden||!T.text){this.labelGlyphCache.delete(y);return}var x=T.text,_=T.fontKey||this.defaultFontKey;this.atlasManager.ensureGlyphs(x,_);var R=[],E=[],L=0,D=M(x),F;try{for(D.s();!(F=D.n()).done;){var A=F.value,I=A.codePointAt(0);if(I===void 0){R.push(void 0),E.push(L);continue}var w=this.atlasManager.getGlyph(I,_);R.push(w),E.push(L),w&&(L+=w.advance)}}catch(k){D.e(k)}finally{D.f()}this.labelGlyphCache.set(y,{glyphs:R,xOffsets:E,totalWidth:L})}},{key:"processCharacter",value:function(y,T,x,_){var R,E,L,D=this.floats,F=this.STRIDE,A=y*F,I=this.labelGlyphCache.get(T.parentKey);if(!I||!I.glyphs[_]){for(var w=0;w<F;w++)D[A+w]=0;return}var k=I.glyphs[_],G=I.xOffsets[_],N=v.labelColor,P=N&&Z(N)==="object"&&"color"in N&&N.color?N.color:T.color,C=ve(P),z=A;D[z++]=T.edgeIndex,D[z++]=(R=(E=this.edgeAttributeTexture)===null||E===void 0?void 0:E.getIndex(T.parentKey))!==null&&R!==void 0?R:0,D[z++]=T.size,D[z++]=G,D[z++]=k.advance,D[z++]=I.totalWidth,D[z++]=Ru(T.position),D[z++]=k.atlasWidth,D[z++]=k.atlasHeight,D[z++]=k.bearingX,D[z++]=-k.bearingY,D[z++]=k.atlasX,D[z++]=k.atlasY,D[z++]=k.atlasWidth,D[z++]=k.atlasHeight;var H=(L=v.labelMargin)!==null&&L!==void 0?L:T.margin;if(D[z++]=H,D[z++]=0,D[z++]=C,h&&o){var U;typeof o.color=="string"?U=o.color:U=o.color.color||"#ffffff",D[z++]=ve(U)}var q=new Set,X=M(l),j;try{for(X.s();!(j=X.n()).done;){var be=j.value,le=M(be.attributes),Re;try{for(le.s();!(Re=le.n()).done;){var qe=Re.value,mt=qe.name.startsWith("a_")?qe.name.slice(2):qe.name;if(mt!=="curvature"&&!q.has(mt)){q.add(mt);for(var bt=0;bt<qe.size;bt++)D[z++]=0}}}catch(yt){le.e(yt)}finally{le.f()}}}catch(yt){X.e(yt)}finally{X.f()}}},{key:"processEdgeLabel",value:function(y,T,x){if(this.prepareLabelGlyphs(y,x),this.edgeAttributeTexture&&!x.hidden&&x.text){this.edgeAttributeTexture.allocate(y);var _=this.packedAttributeData;Rn(this.attrDescriptors,x.edgeAttributes,_,"",Eu,0),this.edgeAttributeTexture.updateAllAttributes(y,_)}return ie(v,"processLabel",this,3)([y,T,x])}},{key:"updateAtlasTexture",value:function(){if(this.atlasNeedsUpdate){var y=this.normalProgram.gl,T=this.atlasManager.getTextures();if(T.length!==0){var x=T[0];y.bindTexture(y.TEXTURE_2D,this.atlasTexture),y.texImage2D(y.TEXTURE_2D,0,y.RGBA,x.width,x.height,0,y.RGBA,y.UNSIGNED_BYTE,x.data),y.bindTexture(y.TEXTURE_2D,null),this.atlasNeedsUpdate=!1}}}},{key:"setUniforms",value:function(y,T){var x=T.gl,_=T.uniformLocations,R=this.atlasManager.getTextures(),E=R.length>0?[R[0].width,R[0].height]:[1,1];if(x.uniformMatrix3fv(_.u_matrix,!1,y.matrix),x.uniform1f(_.u_sizeRatio,y.sizeRatio),x.uniform1f(_.u_correctionRatio,y.correctionRatio),x.uniform1f(_.u_pixelRatio,y.pixelRatio),x.uniform1f(_.u_cameraAngle,y.cameraAngle),x.uniform1f(_.u_sdfBufferPixels,Se.buffer),x.uniform2f(_.u_resolution,y.width,y.height),x.uniform2f(_.u_atlasSize,E[0],E[1]),x.uniform1f(_.u_gamma,this.gamma),x.uniform1f(_.u_sdfBuffer,this.sdfBuffer),x.activeTexture(x.TEXTURE0),x.bindTexture(x.TEXTURE_2D,this.atlasTexture),x.uniform1i(_.u_atlas,0),_.u_nodeDataTexture!==void 0&&x.uniform1i(_.u_nodeDataTexture,y.nodeDataTextureUnit),_.u_nodeDataTextureWidth!==void 0&&x.uniform1i(_.u_nodeDataTextureWidth,y.nodeDataTextureWidth),_.u_edgeDataTexture!==void 0&&x.uniform1i(_.u_edgeDataTexture,y.edgeDataTextureUnit),_.u_edgeDataTextureWidth!==void 0&&x.uniform1i(_.u_edgeDataTextureWidth,y.edgeDataTextureWidth),_.u_edgeFrameTexture!==void 0&&x.uniform1i(_.u_edgeFrameTexture,y.edgeFrameTextureUnit),_.u_edgeFrameTextureWidth!==void 0&&x.uniform1i(_.u_edgeFrameTextureWidth,y.edgeFrameTextureWidth),h&&o&&_.u_borderWidth!==void 0){var L=o.width/Se.buffer*this.sdfBuffer;x.uniform1f(_.u_borderWidth,L)}if(this.edgeAttributeTexture&&_.u_edgeAttributeTexture!==void 0&&(this.edgeAttributeTexture.bind(Ne),x.uniform1i(_.u_edgeAttributeTexture,Ne),x.uniform1i(_.u_edgeAttributeTextureWidth,this.edgeAttributeTexture.getTextureWidth()),x.uniform1i(_.u_edgeAttributeTexelsPerEdge,this.edgeAttributeTexture.getTexelsPerItem())),u==="scaled"&&_.u_zoomSizeRatio!==void 0){var D=this.renderer.getSetting("zoomToSizeRatioFunction"),F=1/D(y.zoomRatio);x.uniform1f(_.u_zoomSizeRatio,F)}}},{key:"renderProgram",value:function(y,T){this.updateAtlasTexture(),this.atlasManager.hasPendingGlyphs()&&(this.atlasManager.flush(),this.updateAtlasTexture()),this.edgeAttributeTexture&&this.edgeAttributeTexture.upload(),ie(v,"renderProgram",this,3)([y,T])}},{key:"registerFont",value:function(y){var T=arguments.length>1&&arguments[1]!==void 0?arguments[1]:"normal",x=arguments.length>2&&arguments[2]!==void 0?arguments[2]:"normal";return this.atlasManager.registerFont({family:y,weight:T,style:x})}},{key:"getAtlasManager",value:function(){return this.atlasManager}},{key:"ensureGlyphsReady",value:function(y,T){var x=T||this.defaultFontKey,_=M(y),R;try{for(_.s();!(R=_.n()).done;){var E=R.value;this.atlasManager.ensureGlyphs(E,x)}}catch(L){_.e(L)}finally{_.f()}this.atlasManager.flush()}},{key:"measureLabelAtlasWidth",value:function(y,T){var x=T||this.defaultFontKey;this.atlasManager.ensureGlyphs(y,x),this.atlasManager.hasPendingGlyphs()&&this.atlasManager.flush();var _=0,R=M(y),E;try{for(R.s();!(E=R.n()).done;){var L=E.value,D=L.codePointAt(0);if(D!==void 0){var F=this.atlasManager.getGlyph(D,x);F&&(_+=F.advance)}}}catch(A){R.e(A)}finally{R.f()}return _}},{key:"measureLabel",value:function(y,T,x){var _=this.measureLabelAtlasWidth(y,x),R=T/Se.fontSize;return{width:_*R,height:T,textHeight:T}}},{key:"kill",value:function(){var y=this.normalProgram.gl;this.refreshTimeout!==null&&(clearTimeout(this.refreshTimeout),this.refreshTimeout=null),this.atlasTexture&&(y.deleteTexture(this.atlasTexture),this.atlasTexture=null),this.edgeAttributeTexture&&(this.edgeAttributeTexture.kill(),this.edgeAttributeTexture=null),this.atlasManager.destroy(),this.labelGlyphCache.clear(),ie(v,"kill",this,3)([])}}])}(Qr);return S(m,"labelColor",r),S(m,"labelMargin",i),new m(a,n,t)}function Du(){var a=`
// No extremity - always returns positive (outside)
float extremity_none(vec2 uv, float lengthRatio, float widthRatio) {
  return 1.0;
}
`;return{name:"none",glsl:a,length:0,widthFactor:1,margin:0,uniforms:[],attributes:[]}}function li(a,n,t,e,r,i,o){var s,l,u=ai(e),d=u.paths,c=u.layers,f=u.defaultHead,h=u.defaultTail,g=[Du()].concat($(u.extremities)),m={},p={};d.forEach(function(A,I){return m[A.name]=I}),g.forEach(function(A,I){return p[A.name]=I});var v=(s=p[f])!==null&&s!==void 0?s:0,b=(l=p[h])!==null&&l!==void 0?l:0,y=null,T=me([].concat($(d),$(c))),x=function(A){function I(w,k,G){var N;Y(this,I),y||(y=Br({paths:d,extremities:g,layers:c,antialias:r})),N=te(this,I,[w,k,G]),S(N,"layerLifecycles",new Map),S(N,"needsShaderRegeneration",!1),S(N,"edgeAttributeTexture",null),S(N,"layout",T),S(N,"attrDescriptors",[]),S(N,"lifecycleIndexOffset",d.length),N._pickingBuffer=k,N.edgeAttributeTexture=new Sn(w,N.layout),N.packedAttributeData=new Float32Array(N.layout.floatsPerItem),c.forEach(function(C,z){if(C.lifecycle){var H={gl:w,renderer:{refresh:function(){return G.refresh()}},getUniformLocation:function(q){return w.getUniformLocation(N.normalProgram.program,q)},requestShaderRegeneration:function(){N.needsShaderRegeneration=!0},requestRefresh:function(){G.refresh()}};N.layerLifecycles.set(z,C.lifecycle(H))}}),N.layerLifecycles.forEach(function(C){var z;return(z=C.init)===null||z===void 0?void 0:z.call(C)});var P=new Map;return N.layerLifecycles.forEach(function(C,z){C.getAttributeData&&P.set(d.length+z,C)}),N.attrDescriptors=En([].concat($(d),$(c)),N.layout,P),N}return ne(I,A),K(I,[{key:"getAttributeTexture",value:function(){return this.edgeAttributeTexture}},{key:"resolveEdgeIds",value:function(k,G,N){var P=k,C=0,z=v,H=b,U=G?P.selfLoopPath:N&&P.parallelPath?P.parallelPath:P.path;U&&m[U]!==void 0&&(C=m[U]),P.head&&P.head!=="none"&&p[P.head]!==void 0&&(z=p[P.head]),P.tail&&P.tail!=="none"&&p[P.tail]!==void 0&&(H=p[P.tail]);var q=g[z],X=g[H];return{pathId:C,headId:z,tailId:H,headLengthRatio:_e(q.length)?0:q.length,tailLengthRatio:_e(X.length)?0:X.length}}},{key:"getDefinition",value:function(){var k=WebGL2RenderingContext,G=k.TRIANGLE_STRIP,N=G,P=y;return{VERTICES:P.verticesPerEdge,VERTEX_SHADER_SOURCE:P.vertexShader,FRAGMENT_SHADER_SOURCE:P.fragmentShader,METHOD:N,UNIFORMS:P.uniforms,ATTRIBUTES:P.attributes,CONSTANT_ATTRIBUTES:P.constantAttributes,CONSTANT_DATA:P.constantData}}},{key:"maybeRegenerateShaders",value:function(){var k=this;if(this.needsShaderRegeneration){this.needsShaderRegeneration=!1;var G=c.map(function(q,X){var j=k.layerLifecycles.get(X);return j!=null&&j.regenerate?j.regenerate():q});y=Br({paths:d,extremities:g,layers:G,antialias:this.renderer.getSetting("antialiasEdges")});var N=this.normalProgram.gl,P=this.normalProgram,C=P.program,z=P.buffer,H=P.vertexShader,U=P.fragmentShader;N.deleteProgram(C),N.deleteBuffer(z),N.deleteShader(H),N.deleteShader(U),this.normalProgram=this.getProgramInfo("normal",N,y.vertexShader,y.fragmentShader,this._pickingBuffer)}}},{key:"process",value:function(k,G,N,P,C,z){var H=G*this.STRIDE;if(C.visibility==="hidden"||N.visibility==="hidden"||P.visibility==="hidden"){for(var U=H+this.STRIDE;H<U;H++)this.floats[H]=0;this.floats[G*this.STRIDE]=Yr;return}this.processVisibleItem(at(k),H,N,P,C,z)}},{key:"processVisibleItem",value:function(k,G,N,P,C,z){var H,U=this.floats,q=this.ints;U[G++]=z,U[G++]=ve(C.color),q[G++]=k,U[G++]=(H=C.opacity)!==null&&H!==void 0?H:1;var X=this.packedAttributeData;Rn(this.attrDescriptors,C,X,C.color,this.layerLifecycles,this.lifecycleIndexOffset),this.edgeAttributeTexture.updateAllAttributesAtRow(z,X)}},{key:"setUniforms",value:function(k,G){var N=this,P=G.gl,C=G.uniformLocations;C.u_matrix&&P.uniformMatrix3fv(C.u_matrix,!1,k.matrix),C.u_sizeRatio&&P.uniform1f(C.u_sizeRatio,k.sizeRatio),C.u_correctionRatio&&P.uniform1f(C.u_correctionRatio,k.correctionRatio),C.u_zoomRatio&&P.uniform1f(C.u_zoomRatio,k.zoomRatio),C.u_pixelRatio&&P.uniform1f(C.u_pixelRatio,k.pixelRatio),C.u_cameraAngle&&P.uniform1f(C.u_cameraAngle,k.cameraAngle),C.u_feather&&P.uniform1f(C.u_feather,k.antiAliasingFeather),C.u_minEdgeThickness&&P.uniform1f(C.u_minEdgeThickness,k.minEdgeThickness),C.u_pickingPadding&&P.uniform1f(C.u_pickingPadding,k.edgePickingPadding),C.u_nodeDataTexture&&P.uniform1i(C.u_nodeDataTexture,k.nodeDataTextureUnit),C.u_nodeDataTextureWidth&&P.uniform1i(C.u_nodeDataTextureWidth,k.nodeDataTextureWidth),C.u_edgeDataTexture&&P.uniform1i(C.u_edgeDataTexture,k.edgeDataTextureUnit),C.u_edgeDataTextureWidth&&P.uniform1i(C.u_edgeDataTextureWidth,k.edgeDataTextureWidth),C.u_edgeFrameTexture&&P.uniform1i(C.u_edgeFrameTexture,k.edgeFrameTextureUnit),C.u_edgeFrameTextureWidth&&P.uniform1i(C.u_edgeFrameTextureWidth,k.edgeFrameTextureWidth),this.edgeAttributeTexture&&this.layout.floatsPerItem>0&&(this.edgeAttributeTexture.bind(Ne),C.u_edgeAttributeTexture&&P.uniform1i(C.u_edgeAttributeTexture,Ne),C.u_edgeAttributeTextureWidth&&P.uniform1i(C.u_edgeAttributeTextureWidth,this.edgeAttributeTexture.getTextureWidth()),C.u_edgeAttributeTexelsPerEdge&&P.uniform1i(C.u_edgeAttributeTexelsPerEdge,this.edgeAttributeTexture.getTexelsPerItem()));var z=new Set;d.forEach(function(H){H.uniforms.forEach(function(U){z.has(U.name)||(z.add(U.name),N.setTypedUniform(U,G))})}),g.forEach(function(H){H.uniforms.forEach(function(U){z.has(U.name)||(z.add(U.name),N.setTypedUniform(U,G))})}),c.forEach(function(H){H.uniforms.forEach(function(U){z.has(U.name)||(z.add(U.name),N.setTypedUniform(U,G))})})}},{key:"render",value:function(k,G,N){this.maybeRegenerateShaders(),ie(I,"render",this,3)([k,G,N])}},{key:"renderProgram",value:function(k,G){this.layerLifecycles.forEach(function(N){var P;return(P=N.beforeRender)===null||P===void 0?void 0:P.call(N)}),ie(I,"renderProgram",this,3)([k,G])}},{key:"uploadAttributeTexture",value:function(){this.edgeAttributeTexture&&this.layout.floatsPerItem>0&&this.edgeAttributeTexture.upload()}},{key:"kill",value:function(){this.layerLifecycles.forEach(function(k){var G;return(G=k.kill)===null||G===void 0?void 0:G.call(k)}),this.edgeAttributeTexture&&(this.edgeAttributeTexture.kill(),this.edgeAttributeTexture=null),ie(I,"kill",this,3)([])}}])}(He),_=g[v],R=g[b],E=B({paths:d,headLengthRatio:_e(_.length)?0:_.length,tailLengthRatio:_e(R.length)?0:R.length},e.label),L=si(E),D=function(){return{labelProgram:Au(a,null,t,E),labelBackgroundProgram:mu(a,n,t,{shaderConfig:L})}},F=new lu(a,{paths:d,extremities:g,layers:c,nodeShapes:i,nodeLayers:o});return{edgeProgram:new x(a,null,t),createLabelPrograms:D,framePass:F}}function wu(a){return Z(a)==="object"&&"uniforms"in a&&Array.isArray(a.uniforms)}function Lu(a){return Z(a)==="object"&&"uniforms"in a&&"attributes"in a&&"glsl"in a}function Cu(a){return Z(a)==="object"&&"uniforms"in a&&"attributes"in a&&"segments"in a}function Pu(a){return Z(a)==="object"&&"uniforms"in a&&"attributes"in a&&"length"in a}function ku(a){return Z(a)==="object"&&"uniforms"in a&&"attributes"in a&&"glsl"in a}function Fu(a){return Z(a)==="object"&&"glsl"in a&&"name"in a&&!("uniforms"in a)}function Iu(a){return Z(a)==="object"&&"glsl"in a&&"name"in a&&!("uniforms"in a)}function Nu(a){return Z(a)==="object"&&"glsl"in a&&"name"in a&&!("uniforms"in a)}function Gu(a){if(wu(a))return a;if(Fu(a))return{name:a.name,glsl:a.glsl,inradiusFactor:a.inradiusFactor,uniforms:[]};throw new Error("Invalid node shape specification: ".concat(JSON.stringify(a)))}function zu(a){if(Lu(a))return a;if(dr(a))return{name:a.name,glsl:a.glsl,uniforms:[],attributes:[]};throw new Error("Invalid node layer specification: ".concat(JSON.stringify(a)))}function Mu(a){if(Cu(a))return a;if(Iu(a))return{name:a.name,glsl:a.glsl,segments:a.segments,uniforms:[],attributes:[]};throw new Error("Invalid edge path specification: ".concat(JSON.stringify(a)))}function Bu(a){if(ku(a))return a;if(cr(a))return{name:a.name,glsl:a.glsl,uniforms:[],attributes:[]};throw new Error("Invalid edge layer specification: ".concat(JSON.stringify(a)))}function Wu(a){if(Pu(a))return a;if(Nu(a))return{name:a.name,glsl:a.glsl,length:a.length,widthFactor:a.widthFactor,margin:0,uniforms:[],attributes:[]};throw new Error("Invalid edge extremity specification: ".concat(JSON.stringify(a)))}function ui(a){var n,t,e=(n=a?.shapes)!==null&&n!==void 0?n:At.shapes,r=(t=a?.layers)!==null&&t!==void 0?t:At.layers,i=e.map(Gu),o=r.map(zu);if(i.length===0)throw new Error("At least one node shape must be specified.");if(o.length===0)throw new Error("At least one node layer must be specified.");return{shapes:i,layers:o}}function Ou(a){var n,t,e,r=(n=a?.paths)!==null&&n!==void 0?n:rt.paths,i=(t=a?.extremities)!==null&&t!==void 0?t:rt.extremities,o=(e=a?.layers)!==null&&e!==void 0?e:rt.layers,s=r.map(Mu),l=i.map(Wu).filter(function(d){return d!==null}),u=o.map(Bu);if(s.length===0)throw new Error("At least one edge path must be specified.");if(u.length===0)throw new Error("At least one edge layer must be specified.");return{paths:s,extremities:l,layers:u}}function di(a,n){var t={},e=M(a),r;try{for(e.s();!(r=e.n()).done;){var i=r.value;i.variables&&Object.assign(t,i.variables)}}catch(o){e.e(o)}finally{e.f()}return Object.assign(t,n||{}),t}function ci(a,n,t,e,r){var i=ui(e),o=i.shapes,s=i.layers,l=di(o,e?.variables),u=ei(a,n,t,{shapes:o,layers:s,label:e?.label,backdrop:e?.backdrop,labelAttachments:e?.labelAttachments},r);return B(B({},u),{},{variables:l})}function hi(a,n,t,e,r,i){var o=Ou(e),s=o.paths,l=o.extremities,u=o.layers,d=ui(i),c=d.shapes,f=d.layers,h=di(s,e?.variables),g=li(a,n,t,{paths:s,extremities:l,layers:u,defaultHead:e?.defaultHead,defaultTail:e?.defaultTail,label:e?.label},r,c,f);return B(B({},g),{},{variables:h,paths:s})}var Uu=2;function fi(a,n,t){var e=arguments.length>3&&arguments[3]!==void 0?arguments[3]:Uu,r=n.canvas,i=r.width,o=r.height,s=t.x,l=t.y,u=t.rowHeight,d=t.maxRowWidth,c={},f=[],h=M(a),g;try{for(h.s();!(g=h.n()).done;){var m=g.value,p=m.width+e,v=m.height+e;if(p>i||v>o||s+p>i&&l+u+v>o){f.push(m);continue}s+p>i&&(d=Math.max(d,s),s=0,l+=u,u=v),m.draw(n,s,l),c[m.key]={x:s,y:l,width:m.width,height:m.height},s+=p,u=Math.max(u,v)}}catch(b){h.e(b)}finally{h.f()}return d=Math.max(d,s),{atlas:c,cursor:{x:s,y:l,rowHeight:u,maxRowWidth:d},remaining:f}}function ue(a,n,t,e){var r=Object.defineProperty;try{r({},"",{})}catch{r=0}ue=function(i,o,s,l){function u(d,c){ue(i,d,function(f){return this._invoke(d,c,f)})}o?r?r(i,o,{value:s,enumerable:!l,configurable:!l,writable:!l}):i[o]=s:(u("next",0),u("throw",1),u("return",2))},ue(a,n,t,e)}function de(){var a,n,t=typeof Symbol=="function"?Symbol:{},e=t.iterator||"@@iterator",r=t.toStringTag||"@@toStringTag";function i(h,g,m,p){var v=g&&g.prototype instanceof s?g:s,b=Object.create(v.prototype);return ue(b,"_invoke",function(y,T,x){var _,R,E,L=0,D=x||[],F=!1,A={p:0,n:0,v:a,a:I,f:I.bind(a,4),d:function(w,k){return _=w,R=0,E=a,A.n=k,o}};function I(w,k){for(R=w,E=k,n=0;!F&&L&&!G&&n<D.length;n++){var G,N=D[n],P=A.p,C=N[2];w>3?(G=C===k)&&(E=N[(R=N[4])?5:(R=3,3)],N[4]=N[5]=a):N[0]<=P&&((G=w<2&&P<N[1])?(R=0,A.v=k,A.n=N[1]):P<C&&(G=w<3||N[0]>k||k>C)&&(N[4]=w,N[5]=k,A.n=C,R=0))}if(G||w>1)return o;throw F=!0,k}return function(w,k,G){if(L>1)throw TypeError("Generator is already running");for(F&&k===1&&I(k,G),R=k,E=G;(n=R<2?a:E)||!F;){_||(R?R<3?(R>1&&(A.n=-1),I(R,E)):A.n=E:A.v=E);try{if(L=2,_){if(R||(w="next"),n=_[w]){if(!(n=n.call(_,E)))throw TypeError("iterator result is not an object");if(!n.done)return n;E=n.value,R<2&&(R=0)}else R===1&&(n=_.return)&&n.call(_),R<2&&(E=TypeError("The iterator does not provide a '"+w+"' method"),R=1);_=a}else if((n=(F=A.n<0)?E:y.call(T,A))!==o)break}catch(N){_=a,R=1,E=N}finally{L=1}}return{value:n,done:F}}}(h,m,p),!0),b}var o={};function s(){}function l(){}function u(){}n=Object.getPrototypeOf;var d=[][e]?n(n([][e]())):(ue(n={},e,function(){return this}),n),c=u.prototype=s.prototype=Object.create(d);function f(h){return Object.setPrototypeOf?Object.setPrototypeOf(h,u):(h.__proto__=u,ue(h,r,"GeneratorFunction")),h.prototype=Object.create(c),h}return l.prototype=u,ue(c,"constructor",u),ue(u,"constructor",l),l.displayName="GeneratorFunction",ue(u,r,"GeneratorFunction"),ue(c),ue(c,r,"Generator"),ue(c,e,function(){return this}),ue(c,"toString",function(){return"[object Generator]"}),(de=function(){return{w:i,m:f}})()}function gi(a,n,t,e,r,i,o){try{var s=a[i](o),l=s.value}catch(u){return void t(u)}s.done?n(l):Promise.resolve(l).then(e,r)}function gt(a){return function(){var n=this,t=arguments;return new Promise(function(e,r){var i=a.apply(n,t);function o(l){gi(i,e,r,o,s,"next",l)}function s(l){gi(i,e,r,o,s,"throw",l)}o(void 0)})}}var Dn=new Map,vi=!1;function Hu(a){return new Promise(function(n,t){var e=new FileReader;e.onload=function(){return n(e.result)},e.onerror=t,e.readAsDataURL(a)})}function $u(a){if(!Dn.has(a)){var n=fetch(a).then(function(t){return t.blob()}).then(Hu).catch(function(){return Dn.delete(a),null});Dn.set(a,n)}return Dn.get(a)}function Vu(a){return ma.apply(this,arguments)}function ma(){return ma=gt(de().m(function a(n){var t,e,r;return de().w(function(i){for(;;)switch(i.n){case 0:return t=document.createElement("div"),t.innerHTML=n,e=Array.from(t.querySelectorAll("img[src]")),r=e.filter(function(o){return!o.getAttribute("src").startsWith("data:")}),i.n=1,Promise.all(r.map(function(){var o=gt(de().m(function s(l){var u;return de().w(function(d){for(;;)switch(d.n){case 0:return d.n=1,$u(l.getAttribute("src"));case 1:u=d.v,u&&l.setAttribute("src",u);case 2:return d.a(2)}},s)}));return function(s){return o.apply(this,arguments)}}()));case 1:return i.a(2,t.innerHTML)}},a)})),ma.apply(this,arguments)}function pi(a){return ba.apply(this,arguments)}function ba(){return ba=gt(de().m(function a(n){var t,e,r,i,o,s,l,u,d,c,f,h,g,m=arguments;return de().w(function(p){for(;;)switch(p.n){case 0:if(t=m.length>1&&m[1]!==void 0?m[1]:1,e=n instanceof SVGElement?new XMLSerializer().serializeToString(n):n,r=new DOMParser,i=r.parseFromString(e,"image/svg+xml"),o=i.querySelector("svg"),o){p.n=1;break}return p.a(2,null);case 1:if(s=parseFloat(o.getAttribute("width")||""),l=parseFloat(o.getAttribute("height")||""),(!(s>0)||!(l>0))&&(u=o.getAttribute("viewBox"),u&&(d=u.trim().split(/[\s,]+/),s=parseFloat(d[2]),l=parseFloat(d[3]))),!(!(s>0)||!(l>0))){p.n=2;break}return console.warn("Sigma: SVG label attachment has no parseable dimensions \u2014 skipped."),p.a(2,null);case 2:return c=Math.ceil(s*t),f=Math.ceil(l*t),h=new Blob([e],{type:"image/svg+xml"}),g=URL.createObjectURL(h),p.a(2,new Promise(function(v){var b=new Image;b.onload=function(){var y=document.createElement("canvas");y.width=c,y.height=f,y.getContext("2d").drawImage(b,0,0,c,f),URL.revokeObjectURL(g);try{y.getContext("2d").getImageData(0,0,1,1)}catch(T){if(T instanceof DOMException&&T.name==="SecurityError"){vi||(vi=!0,console.warn('Sigma: A label attachment was skipped because the rendered canvas is tainted. SVG with <foreignObject> (used by the "html" attachment type) is blocked in Chromium and Safari. Use type: "canvas" with Canvas 2D rendering instead.')),v(null);return}throw T}v(y)},b.onerror=function(){URL.revokeObjectURL(g),v(null)},b.src=g}))}},a)})),ba.apply(this,arguments)}function Xu(a,n){var t=document.createElement("div");t.style.cssText="position:fixed;left:-99999px;top:0;visibility:hidden;width:max-content;height:max-content",t.innerHTML=(n?"<style>".concat(n,"</style>"):"")+a,document.body.appendChild(t);var e=t.getBoundingClientRect(),r=e.width,i=e.height;return document.body.removeChild(t),{width:Math.ceil(r),height:Math.ceil(i)}}function ju(a,n,t,e){return ya.apply(this,arguments)}function ya(){return ya=gt(de().m(function a(n,t,e,r){var i,o,s,l,u,d,c,f,h=arguments;return de().w(function(g){for(;;)switch(g.n){case 0:return i=h.length>4&&h[4]!==void 0?h[4]:1,o=n instanceof HTMLElement?n.outerHTML:n,g.n=1,Vu(o);case 1:return s=g.v,(e==null||r==null)&&(l=Xu(s,t),e=e??l.width,r=r??l.height),u=Math.ceil(e*i),d=Math.ceil(r*i),c=t?"<style>".concat(t,"</style>"):"",f='<svg xmlns="http://www.w3.org/2000/svg" '+'width="'.concat(u,'" height="').concat(d,'" viewBox="0 0 ').concat(e," ").concat(r,'">')+'<foreignObject width="'.concat(e,'" height="').concat(r,'">')+'<body xmlns="http://www.w3.org/1999/xhtml" style="margin:0;padding:0">'.concat(c).concat(s,"</body>")+"</foreignObject></svg>",g.a(2,pi(f,1))}},a)})),ya.apply(this,arguments)}function qu(a){return xa.apply(this,arguments)}function xa(){return xa=gt(de().m(function a(n){var t,e=arguments,r;return de().w(function(i){for(;;)switch(i.n){case 0:t=e.length>1&&e[1]!==void 0?e[1]:1,r=n.type,i.n=r==="canvas"?1:r==="svg"?2:r==="html"?3:4;break;case 1:return i.a(2,n.canvas);case 2:return i.a(2,pi(n.svg,t));case 3:return i.a(2,ju(n.html,n.css,n.width,n.height,t));case 4:return i.a(2)}},a)})),xa.apply(this,arguments)}var ft=2048,mi=function(){function a(n,t,e){Y(this,a),S(this,"cache",new Map),S(this,"pending",new Set),S(this,"atlas",{}),S(this,"glTexture",null),S(this,"dirty",!0),this.gl=n,this.renderers=t,this.scheduleRender=e,this.packCanvas=document.createElement("canvas"),this.packCanvas.width=ft,this.packCanvas.height=ft,this.packCtx=this.packCanvas.getContext("2d")}return K(a,[{key:"renderAttachment",value:function(t,e,r){var i=this,o="".concat(t,":").concat(e);if(!(this.cache.has(o)||this.pending.has(o))){var s=this.renderers[e];if(s){var l=s(r);if(l){this.pending.add(o);var u=r.pixelRatio;Promise.resolve(l).then(function(){var d=gt(de().m(function c(f){var h;return de().w(function(g){for(;;)switch(g.n){case 0:if(i.pending.has(o)){g.n=1;break}return g.a(2);case 1:if(i.pending.delete(o),f){g.n=2;break}return g.a(2);case 2:return g.n=3,qu(f,u);case 3:if(h=g.v,!(!h||h.width===0||h.height===0)){g.n=4;break}return g.a(2);case 4:i.cache.set(o,{image:h,width:h.width,height:h.height}),i.dirty=!0,i.scheduleRender();case 5:return g.a(2)}},c)}));return function(c){return d.apply(this,arguments)}}())}}}}},{key:"regenerateAtlas",value:function(){if(this.dirty){this.dirty=!1;var t=[];if(this.cache.forEach(function(u,d){t.push({key:d,width:u.width,height:u.height,draw:function(f,h,g){f.drawImage(u.image,h,g)}})}),t.length===0){this.atlas={},this.deleteGLTexture();return}var e={x:0,y:0,rowHeight:0,maxRowWidth:0};this.packCtx.clearRect(0,0,ft,ft);var r=fi(t,this.packCtx,e),i=r.atlas,o=r.remaining;this.atlas=i,o.length>0&&console.warn("Sigma: ".concat(o.length," label attachment(s) could not fit in the ").concat(ft,"x").concat(ft," atlas and will not be rendered.")),this.deleteGLTexture();var s=this.gl,l=s.createTexture();s.activeTexture(s.TEXTURE0+It),s.bindTexture(s.TEXTURE_2D,l),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!0),s.texImage2D(s.TEXTURE_2D,0,s.RGBA,s.RGBA,s.UNSIGNED_BYTE,this.packCanvas),s.pixelStorei(s.UNPACK_PREMULTIPLY_ALPHA_WEBGL,!1),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_MIN_FILTER,s.LINEAR),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_MAG_FILTER,s.LINEAR),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_WRAP_S,s.CLAMP_TO_EDGE),s.texParameteri(s.TEXTURE_2D,s.TEXTURE_WRAP_T,s.CLAMP_TO_EDGE),this.glTexture=l}}},{key:"bindTexture",value:function(t){if(this.glTexture){var e=this.gl;e.activeTexture(e.TEXTURE0+t),e.bindTexture(e.TEXTURE_2D,this.glTexture)}}},{key:"getEntry",value:function(t,e){var r="".concat(t,":").concat(e);return this.atlas[r]||null}},{key:"invalidateNode",value:function(t){var e="".concat(t,":"),r=M(this.cache.keys()),i;try{for(r.s();!(i=r.n()).done;){var o=i.value;o.startsWith(e)&&(this.cache.delete(o),this.dirty=!0)}}catch(d){r.e(d)}finally{r.f()}var s=M(this.pending),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;u.startsWith(e)&&this.pending.delete(u)}}catch(d){s.e(d)}finally{s.f()}}},{key:"restore",value:function(){this.glTexture=null,this.dirty=!0}},{key:"clear",value:function(){this.cache.clear(),this.pending.clear(),this.atlas={},this.dirty=!0,this.deleteGLTexture()}},{key:"kill",value:function(){this.clear(),this.packCanvas=null,this.packCtx=null,this.gl=null}},{key:"deleteGLTexture",value:function(){this.glTexture&&(this.gl.deleteTexture(this.glTexture),this.glTexture=null)}}])}(),_a=function(){function a(n){Y(this,a),S(this,"buckets",new Map),S(this,"keyDepth",new Map);var t=M(n),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;this.buckets.set(r,new Set)}}catch(i){t.e(i)}finally{t.f()}}return K(a,[{key:"has",value:function(t){return this.keyDepth.has(t)}},{key:"getBucket",value:function(t){return this.buckets.get(t)}},{key:"set",value:function(t,e){var r,i=this.keyDepth.get(t);if(i!==e){var o=this.buckets.get(e);if(!o)throw new Error('Sigma: "'.concat(e,'" is not a declared depth layer'));i!==void 0&&((r=this.buckets.get(i))===null||r===void 0||r.delete(t)),o.add(t),this.keyDepth.set(t,e)}}},{key:"remove",value:function(t){var e=this.keyDepth.get(t);e!==void 0&&(this.buckets.get(e).delete(t),this.keyDepth.delete(t))}},{key:"clearAll",value:function(){var t=M(this.buckets.values()),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;r.clear()}}catch(i){t.e(i)}finally{t.f()}this.keyDepth.clear()}},{key:"getSorted",value:function(t,e){var r=this.buckets.get(t);return!r||r.size===0?[]:$(r).sort(function(i,o){return e(i)-e(o)})}}])}(),bi=function(a){function n(t,e){return Y(this,n),te(this,n,[t,2,e])}return ne(n,a),K(n,[{key:"updateNode",value:function(e,r,i,o,s,l,u,d){var c=this.indexMap.get(e);if(c===void 0)throw new Error('Node "'.concat(e,'" not allocated in NodeDataTexture'));var f=ke(d),h=Q(f,4),g=h[0],m=h[1],p=h[2],v=h[3],b=c*2*4;this.data[b]=r,this.data[b+1]=i,this.data[b+2]=o,this.data[b+3]=s,this.data[b+4]=l,this.data[b+5]=u,this.data[b+6]=g*65536+m*256+p,this.data[b+7]=v/255,this.markDirty(c)}}])}(Tn),Yu=1024,Ku=1.5,Ta=function(){function a(n,t){var e;if(Y(this,a),S(this,"texture",null),S(this,"framebuffer",null),!n.getExtension("EXT_color_buffer_float"))throw new Error("sigma: EXT_color_buffer_float is required for label/edge placement but is unavailable in this WebGL2 context.");this.gl=n,this.maxTextureSize=n.getParameter(n.MAX_TEXTURE_SIZE),this.channels=t.channels,this.capacity=this.roundUpToPowerOfTwo((e=t.initialCapacity)!==null&&e!==void 0?e:Yu);var r=this.computeDimensions(this.capacity);this.textureWidth=r.width,this.textureHeight=r.height,this.create()}return K(a,[{key:"roundUpToPowerOfTwo",value:function(t){return Math.pow(2,Math.ceil(Math.log2(Math.max(1,t))))}},{key:"computeDimensions",value:function(t){var e=Math.min(t,this.maxTextureSize),r=Math.ceil(t/e);return{width:e,height:r}}},{key:"create",value:function(){var t=this.gl,e=this.channels===1?t.R32F:t.RGBA32F,r=this.channels===1?t.RED:t.RGBA;if(this.texture=t.createTexture(),t.activeTexture(t.TEXTURE0),t.bindTexture(t.TEXTURE_2D,this.texture),t.texImage2D(t.TEXTURE_2D,0,e,this.textureWidth,this.textureHeight,0,r,t.FLOAT,null),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MIN_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_MAG_FILTER,t.NEAREST),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_S,t.CLAMP_TO_EDGE),t.texParameteri(t.TEXTURE_2D,t.TEXTURE_WRAP_T,t.CLAMP_TO_EDGE),this.framebuffer=t.createFramebuffer(),t.bindFramebuffer(t.FRAMEBUFFER,this.framebuffer),t.framebufferTexture2D(t.FRAMEBUFFER,t.COLOR_ATTACHMENT0,t.TEXTURE_2D,this.texture,0),t.checkFramebufferStatus(t.FRAMEBUFFER)!==t.FRAMEBUFFER_COMPLETE)throw new Error("sigma: float framebuffer for frame-pass placement is incomplete.");t.bindFramebuffer(t.FRAMEBUFFER,null),t.bindTexture(t.TEXTURE_2D,null)}},{key:"ensureCapacity",value:function(t){if(!(t<=this.capacity)){var e=this.gl;this.capacity=this.roundUpToPowerOfTwo(Math.ceil(t*Ku));var r=this.computeDimensions(this.capacity);this.textureWidth=r.width,this.textureHeight=r.height,this.texture&&e.deleteTexture(this.texture),this.framebuffer&&e.deleteFramebuffer(this.framebuffer),this.create()}}},{key:"bindAsRenderTarget",value:function(){var t=this.gl;t.bindFramebuffer(t.FRAMEBUFFER,this.framebuffer),t.viewport(0,0,this.textureWidth,this.textureHeight)}},{key:"bind",value:function(t){var e=this.gl;e.activeTexture(e.TEXTURE0+t),e.bindTexture(e.TEXTURE_2D,this.texture)}},{key:"getTexture",value:function(){return this.texture}},{key:"getTextureWidth",value:function(){return this.textureWidth}},{key:"getTextureHeight",value:function(){return this.textureHeight}},{key:"restore",value:function(){this.gl.getExtension("EXT_color_buffer_float"),this.create()}},{key:"kill",value:function(){var t=this.gl;this.texture&&(t.deleteTexture(this.texture),this.texture=null),this.framebuffer&&(t.deleteFramebuffer(this.framebuffer),this.framebuffer=null)}}])}(),yi=function(a){function n(t,e){return Y(this,n),te(this,n,[t,2,e])}return ne(n,a),K(n,[{key:"updateEdge",value:function(e,r,i,o,s,l){var u=arguments.length>6&&arguments[6]!==void 0?arguments[6]:0,d=arguments.length>7&&arguments[7]!==void 0?arguments[7]:0,c=arguments.length>8&&arguments[8]!==void 0?arguments[8]:0,f=this.indexMap.get(e);if(f===void 0)throw new Error('Edge "'.concat(e,'" not allocated in EdgeDataTexture'));var h=f*this.TEXELS_PER_ITEM*4;this.data[h+0]=r,this.data[h+1]=i,this.data[h+2]=o,this.data[h+3]=0,this.data[h+4]=s,this.data[h+5]=l,this.data[h+6]=u,this.data[h+7]=(d&15)<<4|c&15,this.markDirty(f)}}])}(Tn);var Fc=Me(Ke()),Ic=Me(na());function Zu(a,n){if(a==null)return{};var t={};for(var e in a)if({}.hasOwnProperty.call(a,e)){if(n.indexOf(e)!==-1)continue;t[e]=a[e]}return t}function xi(a,n){if(a==null)return{};var t,e,r=Zu(a,n);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(a);for(e=0;e<i.length;e++)t=i[e],n.indexOf(t)===-1&&{}.propertyIsEnumerable.call(a,t)&&(r[t]=a[t])}return r}var Qu=["factor"],Ju=["factor"],_i=1.5,Sa={x:.5,y:.5,angle:0,ratio:1},Ti=function(a){function n(){var t;Y(this,n);for(var e=arguments.length,r=new Array(e),i=0;i<e;i++)r[i]=arguments[i];return t=te(this,n,[].concat(r)),S(t,"minRatio",null),S(t,"maxRatio",null),S(t,"enabled",!0),S(t,"enabledZooming",!0),S(t,"enabledPanning",!0),S(t,"enabledRotation",!0),S(t,"constrainState",null),S(t,"state",B({},Sa)),S(t,"previousState",B({},Sa)),S(t,"nextFrame",null),S(t,"currentAnimationFrom",null),S(t,"currentAnimationTo",null),S(t,"animationCallback",null),t}return ne(n,a),K(n,[{key:"x",get:function(){return this.state.x}},{key:"y",get:function(){return this.state.y}},{key:"angle",get:function(){return this.state.angle}},{key:"ratio",get:function(){return this.state.ratio}},{key:"getState",value:function(){return B({},this.state)}},{key:"getPreviousState",value:function(){return B({},this.previousState)}},{key:"getBoundedRatio",value:function(e){var r=e;return typeof this.minRatio=="number"&&(r=Math.max(r,this.minRatio)),typeof this.maxRatio=="number"&&(r=Math.min(r,this.maxRatio)),r}},{key:"validateState",value:function(e){var r=this.getState();return this.enabledPanning&&typeof e.x=="number"&&(r.x=e.x),this.enabledPanning&&typeof e.y=="number"&&(r.y=e.y),this.enabledZooming&&typeof e.ratio=="number"&&(r.ratio=this.getBoundedRatio(e.ratio)),this.enabledRotation&&typeof e.angle=="number"&&(r.angle=e.angle),this.constrainState?this.constrainState(r):r}},{key:"isAnimating",value:function(){return this.nextFrame!==null}},{key:"setState",value:function(e){if(!this.enabled)return this;var r=this.validateState(e);return Ar(this.state,r)?this:(this.previousState=this.state,this.state=r,this.emit("updated",this.getState()),this)}},{key:"updateState",value:function(e){return this.setState(e(this.getState())),this}},{key:"animate",value:function(e,r){var i=this;return this.enabled?new Promise(function(o){return i.runAnimation(e,B(B({},Lr),r),o)}):Promise.resolve()}},{key:"cancelAnimation",value:function(){return this.nextFrame!==null&&(cancelAnimationFrame(this.nextFrame),this.nextFrame=null),this.resolveAnimation(),this.emitAnimationEnd(!1),this}},{key:"zoomIn",value:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},r=e.factor,i=r===void 0?_i:r,o=xi(e,Qu);return this.animate({ratio:this.ratio/i},o)}},{key:"zoomOut",value:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:{},r=e.factor,i=r===void 0?_i:r,o=xi(e,Ju);return this.animate({ratio:this.ratio*i},o)}},{key:"reset",value:function(e){return this.animate(Sa,e)}},{key:"runAnimation",value:function(e,r,i){var o=this,s=rn(r.easing),l=Date.now(),u=this.getState(),d=this.validateState(e),c=function(){if(!o.enabled){o.cancelAnimation();return}var h=r.duration>0?(Date.now()-l)/r.duration:1;if(h>=1){o.nextFrame=null,o.setState(d),o.resolveAnimation(),o.emitAnimationEnd(!0);return}var g=s(h);o.setState({x:u.x+(d.x-u.x)*g,y:u.y+(d.y-u.y)*g,angle:u.angle+(d.angle-u.angle)*g,ratio:u.ratio+(d.ratio-u.ratio)*g}),o.nextFrame=requestAnimationFrame(c)};this.cancelAnimation(),this.currentAnimationFrom=u,this.currentAnimationTo=d,this.animationCallback=i,this.emit("animationStart",{from:u,to:d}),c()}},{key:"resolveAnimation",value:function(){var e=this.animationCallback;this.animationCallback=null,e&&e()}},{key:"emitAnimationEnd",value:function(e){var r=this.currentAnimationFrom,i=this.currentAnimationTo;!r||!i||(this.currentAnimationFrom=null,this.currentAnimationTo=null,this.emit("animationEnd",{from:r,to:i,completed:e}))}}],[{key:"from",value:function(e){var r=new n;return r.setState(e)}}])}(un);function ce(a,n){var t=n.getBoundingClientRect();return{x:a.clientX-t.left,y:a.clientY-t.top}}function Ee(a,n){var t=B(B({},ce(a,n)),{},{sigmaDefaultPrevented:!1,preventSigmaDefault:function(){t.sigmaDefaultPrevented=!0},original:a});return t}function $e(a){var n="x"in a?a:B(B({},a.touches[0]||a.previousTouches[0]),{},{original:a.original,sigmaDefaultPrevented:a.sigmaDefaultPrevented,preventSigmaDefault:function(){a.sigmaDefaultPrevented=!0,n.sigmaDefaultPrevented=!0}});return n}function ed(a,n){var t=Ee(a,n);return t.delta=Mi(a),t}var td=2;function Cn(a){for(var n=[],t=0,e=Math.min(a.length,td);t<e;t++)n.push(a[t]);return n}function Gt(a,n,t){var e={touches:Cn(a.touches).map(function(r){return ce(r,t)}),previousTouches:n.map(function(r){return ce(r,t)}),sigmaDefaultPrevented:!1,preventSigmaDefault:function(){e.sigmaDefaultPrevented=!0},original:a};return e}function Mi(a){if(typeof a.deltaY<"u")return a.deltaY*-3/360;if(typeof a.detail<"u")return a.detail/-9;throw new Error("Captor: could not extract delta from event.")}var Bi=function(a){function n(t,e){var r;return Y(this,n),r=te(this,n),r.container=t,r.renderer=e,r}return ne(n,a),K(n)}(un),nd=["doubleClickTimeout","doubleClickZoomingDuration","doubleClickZoomingRatio","dragTimeout","draggedEventsTolerance","enableCameraMouseRotation","gestureTarget","inertiaDuration","inertiaRatio","zoomDuration","zoomingRatio"],ad=nd.reduce(function(a,n){return B(B({},a),{},S({},n,hn[n]))},{});function zt(a){return a instanceof PointerEvent&&a.pointerType==="touch"}var rd=function(a){function n(t,e){var r;return Y(this,n),r=te(this,n,[t,e]),S(r,"enabled",!0),S(r,"draggedEvents",0),S(r,"downStartTime",null),S(r,"lastMouseX",null),S(r,"lastMouseY",null),S(r,"isMouseDown",!1),S(r,"isMoving",!1),S(r,"isPanningStage",!1),S(r,"movingTimeout",null),S(r,"startCameraState",null),S(r,"clicks",0),S(r,"doubleClickTimeout",null),S(r,"isRightMouseDown",!1),S(r,"startRotationAngle",null),S(r,"startCameraAngle",null),S(r,"currentWheelDirection",0),S(r,"lastWheelAnimationId",0),S(r,"settings",ad),r.handleRightClick=r.handleRightClick.bind(r),r.handleDown=r.handleDown.bind(r),r.handleUp=r.handleUp.bind(r),r.handleMove=r.handleMove.bind(r),r.handleWheel=r.handleWheel.bind(r),r.handleLeave=r.handleLeave.bind(r),r.handleEnter=r.handleEnter.bind(r),t.addEventListener("contextmenu",r.handleRightClick,{capture:!1}),t.addEventListener("pointerdown",r.handleDown,{capture:!1}),t.addEventListener("wheel",r.handleWheel,{capture:!1,passive:!1}),t.addEventListener("pointerleave",r.handleLeave,{capture:!1}),t.addEventListener("pointerenter",r.handleEnter,{capture:!1}),document.addEventListener("pointermove",r.handleMove,{capture:!1}),document.addEventListener("pointerup",r.handleUp,{capture:!1}),r}return ne(n,a),K(n,[{key:"kill",value:function(){var e=this.container;e.removeEventListener("contextmenu",this.handleRightClick),e.removeEventListener("pointerdown",this.handleDown),e.removeEventListener("wheel",this.handleWheel),e.removeEventListener("pointerleave",this.handleLeave),e.removeEventListener("pointerenter",this.handleEnter),document.removeEventListener("pointermove",this.handleMove),document.removeEventListener("pointerup",this.handleUp)}},{key:"handleClick",value:function(e){var r=this;if(this.enabled){if(this.clicks++,this.clicks===2)return this.clicks=0,typeof this.doubleClickTimeout=="number"&&(clearTimeout(this.doubleClickTimeout),this.doubleClickTimeout=null),this.handleDoubleClick(e);setTimeout(function(){r.clicks=0,r.doubleClickTimeout=null},this.settings.doubleClickTimeout),this.draggedEvents<this.settings.draggedEventsTolerance&&this.emit("click",Ee(e,this.container))}}},{key:"handleRightClick",value:function(e){this.enabled&&(this.settings.enableCameraMouseRotation&&e.preventDefault(),this.emit("rightClick",Ee(e,this.container)))}},{key:"handleDoubleClick",value:function(e){if(this.enabled){e.preventDefault(),e.stopPropagation();var r=Ee(e,this.container);if(this.emit("doubleClick",r),!r.sigmaDefaultPrevented){var i=this.renderer.getCamera(),o=i.getBoundedRatio(i.getState().ratio/this.settings.doubleClickZoomingRatio);i.animate(this.renderer.getViewportZoomedState(ce(e,this.container),o),{easing:"quadraticInOut",duration:this.settings.doubleClickZoomingDuration})}}}},{key:"handleDown",value:function(e){if(!(!this.enabled||zt(e))){if(e.button===0){this.startCameraState=this.renderer.getCamera().getState();var r=ce(e,this.container),i=r.x,o=r.y;this.lastMouseX=i,this.lastMouseY=o,this.draggedEvents=0,this.downStartTime=Date.now(),this.isMouseDown=!0}if(e.button===2&&this.settings.enableCameraMouseRotation){var s=ce(e,this.container),l=s.x,u=s.y,d=this.container.offsetWidth/2,c=this.container.offsetHeight/2;this.startRotationAngle=Math.atan2(u-c,l-d),this.startCameraAngle=this.renderer.getCamera().getState().angle,this.isRightMouseDown=!0}this.emit("mousedown",Ee(e,this.container))}}},{key:"handleUp",value:function(e){var r=this;if(!(!this.enabled||zt(e)||!this.isMouseDown&&!this.isRightMouseDown)){if(this.isRightMouseDown){this.isRightMouseDown=!1,this.startRotationAngle=null,this.startCameraAngle=null,this.emit("mouseup",Ee(e,this.container));return}var i=this.renderer.getCamera();this.isMouseDown=!1,this.isPanningStage&&(this.isPanningStage=!1,this.renderer._setPanning(!1)),typeof this.movingTimeout=="number"&&(clearTimeout(this.movingTimeout),this.movingTimeout=null);var o=ce(e,this.container),s=o.x,l=o.y,u=i.getState(),d=i.getPreviousState();this.isMoving?i.animate({x:u.x+this.settings.inertiaRatio*(u.x-d.x),y:u.y+this.settings.inertiaRatio*(u.y-d.y)},{duration:this.settings.inertiaDuration,easing:"quadraticOut"}):(this.lastMouseX!==s||this.lastMouseY!==l)&&i.setState({x:u.x,y:u.y}),this.isMoving=!1,setTimeout(function(){var c=r.draggedEvents>0;r.draggedEvents=0;var f=r.renderer.getSetting("hideEdgesOnMove")||r.renderer.getSetting("hideLabelsOnMove");c&&f&&r.renderer.refresh()},0),this.emit("mouseup",Ee(e,this.container)),(e.target===this.container||e.composedPath()[0]===this.container)&&this.handleClick(e)}}},{key:"handleMove",value:function(e){var r=this;if(!(!this.enabled||zt(e))){var i=Ee(e,this.container);if(this.emit("mousemovebody",i),(e.target===this.container||e.composedPath()[0]===this.container)&&this.emit("mousemove",i),this.isMouseDown&&this.draggedEvents++,!i.sigmaDefaultPrevented){if(this.isMouseDown){this.isMoving=!0,typeof this.movingTimeout=="number"&&clearTimeout(this.movingTimeout),this.movingTimeout=window.setTimeout(function(){r.movingTimeout=null,r.isMoving=!1},this.settings.dragTimeout);var o=this.renderer.getCamera(),s=ce(e,this.container),l=s.x,u=s.y,d=this.renderer.viewportToFramedGraph({x:this.lastMouseX,y:this.lastMouseY}),c=this.renderer.viewportToFramedGraph({x:l,y:u}),f=d.x-c.x,h=d.y-c.y,g=o.getState(),m=g.x+f,p=g.y+h;this.isPanningStage||(this.isPanningStage=!0,this.renderer._setPanning(!0)),o.setState({x:m,y:p}),this.lastMouseX=l,this.lastMouseY=u,e.preventDefault(),e.stopPropagation()}if(this.isRightMouseDown){var v=ce(e,this.container),b=v.x,y=v.y,T=this.container.offsetWidth/2,x=this.container.offsetHeight/2,_=Math.atan2(y-x,b-T),R=_-this.startRotationAngle,E=this.renderer.getCamera();E.setState({angle:this.startCameraAngle+R}),e.preventDefault(),e.stopPropagation()}}}}},{key:"handleLeave",value:function(e){zt(e)||this.emit("mouseleave",Ee(e,this.container))}},{key:"handleEnter",value:function(e){zt(e)||this.emit("mouseenter",Ee(e,this.container))}},{key:"handleWheel",value:function(e){var r=this,i=this.renderer.getCamera();if(!(!this.enabled||!i.enabledZooming)){var o=ed(e,this.container);if(this.emit("wheel",o),!o.sigmaDefaultPrevented){var s=this.settings.gestureTarget;if(s!=="page"){if(s==="shared"&&!e.ctrlKey&&!e.metaKey){this.renderer._showGestureHint("wheel");return}var l=Mi(e);if(l){e.preventDefault(),e.stopPropagation();var u=i.getState().ratio,d=l>0?1/this.settings.zoomingRatio:this.settings.zoomingRatio,c=i.getBoundedRatio(u*d),f=l>0?1:-1,h=Date.now();if(u!==c&&!(this.currentWheelDirection===f&&this.lastWheelTriggerTime&&h-this.lastWheelTriggerTime<this.settings.zoomDuration/5)){var g=++this.lastWheelAnimationId;i.animate(this.renderer.getViewportZoomedState(ce(e,this.container),c),{easing:"quadraticOut",duration:this.settings.zoomDuration}).then(function(){r.lastWheelAnimationId===g&&(r.currentWheelDirection=0)}),this.currentWheelDirection=f,this.lastWheelTriggerTime=h}}}}}}},{key:"setSettings",value:function(e){this.settings=e}}])}(Bi),id=["dragTimeout","gestureTarget","inertiaDuration","inertiaRatio","doubleClickTimeout","doubleClickZoomingRatio","doubleClickZoomingDuration","tapMoveTolerance"],od=id.reduce(function(a,n){return B(B({},a),{},S({},n,hn[n]))},{}),sd=function(a){function n(t,e){var r;return Y(this,n),r=te(this,n,[t,e]),S(r,"enabled",!0),S(r,"isMoving",!1),S(r,"hasMoved",!1),S(r,"isPanningStage",!1),S(r,"isZoomingStage",!1),S(r,"touchMode",0),S(r,"startTouchesPositions",[]),S(r,"lastTouches",[]),S(r,"lastTap",null),S(r,"settings",od),r.handleStart=r.handleStart.bind(r),r.handleLeave=r.handleLeave.bind(r),r.handleMove=r.handleMove.bind(r),t.addEventListener("touchstart",r.handleStart,{capture:!1}),t.addEventListener("touchcancel",r.handleLeave,{capture:!1}),document.addEventListener("touchend",r.handleLeave,{capture:!1,passive:!1}),document.addEventListener("touchmove",r.handleMove,{capture:!1,passive:!1}),r}return ne(n,a),K(n,[{key:"kill",value:function(){var e=this.container;e.removeEventListener("touchstart",this.handleStart),e.removeEventListener("touchcancel",this.handleLeave),document.removeEventListener("touchend",this.handleLeave),document.removeEventListener("touchmove",this.handleMove)}},{key:"getDimensions",value:function(){return{width:this.container.offsetWidth,height:this.container.offsetHeight}}},{key:"doesCapture",value:function(e){var r=this.settings.gestureTarget;return r==="graph"?!0:r==="page"?!1:e>=2}},{key:"syncStageFlags",value:function(){var e=this.touchMode===1&&this.hasMoved,r=this.touchMode===2;e!==this.isPanningStage&&(this.isPanningStage=e,this.renderer._setPanning(e)),r!==this.isZoomingStage&&(this.isZoomingStage=r,this.renderer._setZooming(r))}},{key:"handleStart",value:function(e){var r=this;if(this.enabled){var i=Cn(e.touches);if(this.touchMode=i.length,this.startCameraState=this.renderer.getCamera().getState(),this.startTouchesPositions=i.map(function(h){return ce(h,r.container)}),this.touchMode===2){var o=Q(this.startTouchesPositions,2),s=o[0],l=s.x,u=s.y,d=o[1],c=d.x,f=d.y;this.startTouchesAngle=Math.atan2(f-u,c-l),this.startTouchesDistance=Math.sqrt(Math.pow(c-l,2)+Math.pow(f-u,2))}this.syncStageFlags(),this.emit("touchdown",Gt(e,this.lastTouches,this.container)),this.lastTouches=i,this.lastTouchesPositions=this.startTouchesPositions,e.cancelable&&(this.doesCapture(e.touches.length)||this.renderer._hasNodeDrag())&&e.preventDefault()}}},{key:"handleLeave",value:function(e){if(!(!this.enabled||!this.startTouchesPositions.length)){switch(e.cancelable&&this.doesCapture(this.touchMode)&&e.preventDefault(),this.movingTimeout&&(this.isMoving=!1,clearTimeout(this.movingTimeout)),this.touchMode){case 2:if(e.touches.length===1){this.handleStart(e);break}case 1:if(this.isMoving){var r=this.renderer.getCamera(),i=r.getState(),o=r.getPreviousState();r.animate({x:i.x+this.settings.inertiaRatio*(i.x-o.x),y:i.y+this.settings.inertiaRatio*(i.y-o.y)},{duration:this.settings.inertiaDuration,easing:"quadraticOut"})}this.hasMoved=!1,this.isMoving=!1,this.touchMode=0;break}if(this.syncStageFlags(),this.emit("touchup",Gt(e,this.lastTouches,this.container)),!e.touches.length){var s=ce(this.lastTouches[0],this.container),l=this.startTouchesPositions[0],u=Math.pow(s.x-l.x,2)+Math.pow(s.y-l.y,2);if(!e.touches.length&&u<Math.pow(this.settings.tapMoveTolerance,2))if(this.lastTap&&Date.now()-this.lastTap.time<this.settings.doubleClickTimeout){var d=Gt(e,this.lastTouches,this.container);if(this.emit("doubletap",d),this.lastTap=null,!d.sigmaDefaultPrevented&&this.settings.gestureTarget!=="page"){var c=this.renderer.getCamera(),f=c.getBoundedRatio(c.getState().ratio/this.settings.doubleClickZoomingRatio);c.animate(this.renderer.getViewportZoomedState(s,f),{easing:"quadraticInOut",duration:this.settings.doubleClickZoomingDuration})}}else{var h=Gt(e,this.lastTouches,this.container);this.emit("tap",h),this.lastTap={time:Date.now(),position:h.touches[0]||h.previousTouches[0]}}}this.lastTouches=Cn(e.touches),this.startTouchesPositions=[]}}},{key:"handleMove",value:function(e){var r=this;if(!(!this.enabled||!this.startTouchesPositions.length)){var i=this.doesCapture(e.touches.length);i&&e.preventDefault();var o=Cn(e.touches),s=o.map(function(U){return ce(U,r.container)}),l=this.lastTouches;this.lastTouches=o,this.lastTouchesPositions=s;var u=Gt(e,l,this.container);if(this.emit("touchmove",u),!u.sigmaDefaultPrevented&&(this.hasMoved||(this.hasMoved=s.some(function(U,q){var X=r.startTouchesPositions[q];return X&&(U.x!==X.x||U.y!==X.y)})),!!this.hasMoved)){if(!i){this.settings.gestureTarget==="shared"&&this.renderer._showGestureHint("touch");return}this.isMoving=!0,this.syncStageFlags(),this.movingTimeout&&clearTimeout(this.movingTimeout),this.movingTimeout=window.setTimeout(function(){r.isMoving=!1},this.settings.dragTimeout);var d=this.renderer.getCamera(),c=this.startCameraState,f=this.renderer.getSetting("stagePadding");switch(this.touchMode){case 1:{var h=this.renderer.viewportToFramedGraph((this.startTouchesPositions||[])[0]),g=h.x,m=h.y,p=this.renderer.viewportToFramedGraph(s[0]),v=p.x,b=p.y;d.setState({x:c.x+g-v,y:c.y+m-b});break}case 2:{var y={x:.5,y:.5,angle:0,ratio:1},T=s[0],x=T.x,_=T.y,R=s[1],E=R.x,L=R.y,D=Math.atan2(L-_,E-x)-this.startTouchesAngle,F=Math.hypot(L-_,E-x)/this.startTouchesDistance,A=d.getBoundedRatio(c.ratio/F);y.ratio=A,y.angle=c.angle+D;var I=this.getDimensions(),w=this.renderer.viewportToFramedGraph((this.startTouchesPositions||[])[0],{cameraState:c}),k=Math.min(I.width,I.height)-2*f,G=k/I.width,N=k/I.height,P=A/k,C=x-k/2/G,z=_-k/2/N,H=Mn({x:C,y:z},y.angle);C=H.x,z=H.y,y.x=w.x-C*P,y.y=w.y+z*P,d.setState(y);break}}}}}},{key:"setSettings",value:function(e){this.settings=e}}])}(Bi),ld=function(){function a(n,t,e,r){Y(this,a),S(this,"pendingNode",null),S(this,"session",null),this.graph=n,this.viewportToGraph=t,this.setNodesState=e,this.emit=r}return K(a,[{key:"start",value:function(t,e,r,i,o){var s=r(t),l=!1;if(this.emit("nodeDragStart",{node:t,allDraggedNodes:s,event:e,preventSigmaDefault:function(){l=!0}}),l)return!1;var u=new Map,d=M(s),c;try{for(d.s();!(c=d.n()).done;){var f=c.value;u.set(f,{x:this.graph.getNodeAttribute(f,i),y:this.graph.getNodeAttribute(f,o)})}}catch(h){d.e(h)}finally{d.f()}return this.session={node:t,allNodes:s,startPosition:this.viewportToGraph(e),startNodePositions:u,xAttr:i,yAttr:o},this.setNodesState(s,{isDragged:!0}),!0}},{key:"applyMove",value:function(t,e){var r=this.session,i=r.allNodes,o=r.startNodePositions,s=r.startPosition,l=r.xAttr,u=r.yAttr,d=this.viewportToGraph(t),c={x:d.x-s.x,y:d.y-s.y},f=M(i),h;try{for(f.s();!(h=f.n()).done;){var g=h.value,m=o.get(g);if(!(!m||!this.graph.hasNode(g))){var p={x:m.x+c.x,y:m.y+c.y};e?this.graph.mergeNodeAttributes(g,e(p,g)):(this.graph.setNodeAttribute(g,l,p.x),this.graph.setNodeAttribute(g,u,p.y))}}}catch(v){f.e(v)}finally{f.f()}}},{key:"end",value:function(){if(this.pendingNode=null,!this.session)return null;var t=this.session,e=t.node,r=t.allNodes;return this.setNodesState(r,{isDragged:!1}),this.session=null,{node:e,allNodes:r}}},{key:"removeNode",value:function(t){t===this.pendingNode&&(this.pendingNode=null),this.session&&(this.session.node===t?(this.setNodesState(this.session.allNodes,{isDragged:!1}),this.session=null):this.session.allNodes.includes(t)&&(this.session.allNodes=this.session.allNodes.filter(function(e){return e!==t}),this.session.startNodePositions.delete(t)))}},{key:"clear",value:function(){this.pendingNode=null,this.session=null}}])}();function Si(a,n){return a<n?"".concat(a,"\0").concat(n):"".concat(n,"\0").concat(a)}var ud=function(){function a(n,t){Y(this,a),S(this,"groups",new Map),S(this,"edgeToGroupKey",new Map),this.graph=n,this.onGroupChanged=t}return K(a,[{key:"getGroupKey",value:function(t){return Si(this.graph.source(t),this.graph.target(t))}},{key:"sortGroup",value:function(t,e){var r=this,i=e.split("\0")[0];t.sort(function(o,s){var l=r.graph.source(o)===i||!r.graph.isDirected(o)?0:1,u=r.graph.source(s)===i||!r.graph.isDirected(s)?0:1;return l-u})}},{key:"register",value:function(t){var e=this.getGroupKey(t),r=this.groups.get(e);r||(r=[],this.groups.set(e,r)),r.includes(t)||r.push(t),this.edgeToGroupKey.set(t,e),r.length>1&&this.sortGroup(r,e),this.onGroupChanged(r,r.length)}},{key:"unregister",value:function(t){var e=this.edgeToGroupKey.get(t);if(e){this.edgeToGroupKey.delete(t);var r=this.groups.get(e);if(r){var i=r.indexOf(t);i!==-1&&r.splice(i,1),r.length===0?this.groups.delete(e):this.onGroupChanged(r,r.length)}}}},{key:"getGroup",value:function(t){var e,r=this.edgeToGroupKey.get(t);return r?(e=this.groups.get(r))!==null&&e!==void 0?e:[]:[]}},{key:"getSiblings",value:function(t){return this.getGroup(t).filter(function(e){return e!==t})}},{key:"rebuild",value:function(){var t=this;this.groups.clear(),this.edgeToGroupKey.clear(),this.graph.forEachEdge(function(l,u,d,c){var f=Si(d,c),h=t.groups.get(f);h||(h=[],t.groups.set(f,h)),h.push(l),t.edgeToGroupKey.set(l,f)});var e=M(this.groups),r;try{for(e.s();!(r=e.n()).done;){var i=Q(r.value,2),o=i[0],s=i[1];s.length>1&&this.sortGroup(s,o),this.onGroupChanged(s,s.length)}}catch(l){e.e(l)}finally{e.f()}}},{key:"clear",value:function(){this.groups.clear(),this.edgeToGroupKey.clear()}}])}();function Ei(a,n){var t;if(a===!1||a==="extend"||a==="separate")return a;var e=a[n];return e!==void 0?e:(t=a.default)!==null&&t!==void 0?t:!1}function Ri(a){return a===!1?!1:a==="extend"||a==="separate"?!0:Object.values(a).some(function(n){return n==="extend"||n==="separate"})}function Ai(a){return a==="separate"?!0:a===!1||a==="extend"?!1:a.default==="separate"?!0:Object.values(a).includes("separate")}var se={node:{parent:null,eventSuffix:"Node",payloadKey:"node",isEnabled:function(){return!0},writesPickingThisFrame:function(){return!0},setHover:function(n,t,e){return n.setNodeState(t,{isHovered:e})},getCursor:function(n,t){var e;return(e=n.nodeDataCache[t])===null||e===void 0?void 0:e.cursor},isHitValid:function(n,t){var e;return((e=n.nodeDataCache[t])===null||e===void 0?void 0:e.visibility)!=="hidden"}},edge:{parent:null,eventSuffix:"Edge",payloadKey:"edge",isEnabled:function(n){return!!n.settings.enableEdgeEvents},writesPickingThisFrame:function(n){return!!n.settings.enableEdgeEvents},setHover:function(n,t,e){return n.setEdgeState(t,{isHovered:e})},getCursor:function(n,t){var e;return(e=n.edgeDataCache[t])===null||e===void 0?void 0:e.cursor}},nodeLabel:{parent:"node",eventSuffix:"NodeLabel",payloadKey:"node",isEnabled:function(n){return Ai(n.settings.nodeLabelEvents)},writesPickingThisFrame:function(n){return Ri(n.settings.nodeLabelEvents)},setHover:function(n,t,e){return n.setNodeState(t,{isLabelHovered:e})},getCursor:function(n,t){var e;return(e=n.nodeDataCache[t])===null||e===void 0?void 0:e.labelCursor},resolveForVerb:function(n,t,e){var r=Ei(e.settings.nodeLabelEvents,t);return r===!1?null:r==="extend"?{kind:"node",key:n.key}:n}},edgeLabel:{parent:"edge",eventSuffix:"EdgeLabel",payloadKey:"edge",isEnabled:function(n){return Ai(n.settings.edgeLabelEvents)},writesPickingThisFrame:function(n){return Ri(n.settings.edgeLabelEvents)},setHover:function(n,t,e){return n.setEdgeState(t,{isLabelHovered:e})},getCursor:function(n,t){var e;return(e=n.edgeDataCache[t])===null||e===void 0?void 0:e.labelCursor},resolveForVerb:function(n,t,e){var r=Ei(e.settings.edgeLabelEvents,t);return r===!1?null:r==="extend"?{kind:"edge",key:n.key}:n}}},je=["node","edge","nodeLabel","edgeLabel"];function dd(){return{lookup:[null],idsByKind:{node:new Map,edge:new Map,nodeLabel:new Map,edgeLabel:new Map},nextId:1}}function Xe(a,n,t){var e;return(e=a.idsByKind[n].get(t))!==null&&e!==void 0?e:0}function wn(a,n){var t=M(je),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;if(r===n||se[r].parent===n){var i=M(a.idsByKind[r].values()),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;a.lookup[s]=null}}catch(f){i.e(f)}finally{i.f()}a.idsByKind[r]=new Map}}}catch(f){t.e(f)}finally{t.f()}var l=1,u=M(je),d;try{for(u.s();!(d=u.n()).done;){var c=d.value;if(c===n)break;l+=a.idsByKind[c].size}}catch(f){u.e(f)}finally{u.f()}a.nextId=l}function Di(a,n,t){var e=a.nextId++;return a.idsByKind[n].set(t,e),a.lookup[e]={kind:n,key:t},e}function wi(a,n,t){for(var e=0,r=Pn(n);e<r.length;e++){var i=r[e],o=a.idsByKind[i].get(t);o!==void 0&&(a.lookup[o]=null,a.idsByKind[i].delete(t))}}function cd(a,n){var t=M(je),e;try{for(t.s();!(e=t.n()).done;){var r=e.value;if(se[r].parent!==null){var i=M(a.idsByKind[r].values()),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;a.lookup[s]=null}}catch(x){i.e(x)}finally{i.f()}a.idsByKind[r]=new Map}}}catch(x){t.e(x)}finally{t.f()}a.nextId=1;var l=M(je),u;try{for(l.s();!(u=l.n()).done;){var d=u.value;if(se[d].parent===null){var c=M(a.idsByKind[d].values()),f;try{for(c.s();!(f=c.n()).done;){var h=f.value;h>=a.nextId&&(a.nextId=h+1)}}catch(x){c.e(x)}finally{c.f()}}}}catch(x){l.e(x)}finally{l.f()}var g=M(je),m;try{for(g.s();!(m=g.n()).done;){var p=m.value,v=se[p];if(!(v.parent===null||!v.isEnabled(n))){var b=M(a.idsByKind[v.parent].keys()),y;try{for(b.s();!(y=b.n()).done;){var T=y.value;a.idsByKind[p].set(T,a.nextId),a.lookup[a.nextId]={kind:p,key:T},a.nextId++}}catch(x){b.e(x)}finally{b.f()}}}}catch(x){g.e(x)}finally{g.f()}}function hd(a,n){var t=M(je),e;try{for(t.s();!(e=t.n()).done;){var r=e.value,i=a[r],o=n[r];if(i!==o){if(i.size!==o.size)return!1;var s=M(i),l;try{for(s.s();!(l=s.n()).done;){var u=Q(l.value,2),d=u[0],c=u[1];if(o.get(d)!==c)return!1}}catch(f){s.e(f)}finally{s.f()}}}}catch(f){t.e(f)}finally{t.f()}return!0}function Li(a,n,t){se[n.kind].setHover(a,n.key,t)}function fd(a,n){return se[n.kind].getCursor(a,n.key)}function Mt(a,n){return"".concat(n).concat(se[a].eventSuffix)}function Bt(a,n){return B(B({},n),{},S({},se[a.kind].payloadKey,a.key))}function gd(a,n,t){var e=se[n.kind].resolveForVerb;return e?e(n,t,a):n}function vd(a,n){var t=se[n.kind].isHitValid;return t?t(a,n.key):!0}function Pn(a){return je.filter(function(n){return n===a||se[n].parent===a})}function Wi(a,n,t){return n&&(n=gd(a,n,t)),n&&!vd(a,n)&&(n=null),n}function Ea(a,n,t){var e=t==="wheel"?a.stateManager.hovered:a.getHitAtPosition(n);return Wi(a,e,t)}function pd(a,n){return!a||!n?a===n:a.kind===n.kind&&a.key===n.key}function Oi(a,n,t){var e={event:t,preventSigmaDefault:function(){return t.preventSigmaDefault()}},r=a.dragManager.session,i=r?{kind:"node",key:r.node}:Wi(a,n,"enter"),o=a.stateManager,s=o.hovered;pd(s,i)||(s&&(Li(a,s,!1),a.emit(Mt(s.kind,"leave"),Bt(s,e))),o.setHovered(i),i&&(Li(a,i,!0),a.emit(Mt(i.kind,"enter"),Bt(i,e))),a.updateContainerCursor())}function md(a,n,t,e){e.handleResize=function(){return a.scheduleRefresh()},window.addEventListener("resize",e.handleResize),e.handleMove=function(i){a.hoverResolver.pointerMoved($e(i))},e.handleMoveBody=function(i){var o=$e(i),s=a.dragManager;if(s.pendingNode&&!s.session){var l=a.nodeStyleAnalysis,u=l.xAttribute,d=l.yAttribute,c=a.settings;s.start(s.pendingNode,o,c.getDraggedNodes,u||"x",d||"y"),s.pendingNode=null}s.session&&(s.applyMove(o,a.settings.dragPositionToAttributes),a.emit("nodeDrag",{node:s.session.node,allDraggedNodes:s.session.allNodes,event:o}),o.preventSigmaDefault()),a.emit("moveBody",{event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}})},e.handleLeave=function(i){var o=$e(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}};a.hoverResolver.pointerLeft(),Oi(a,null,o),a.emit("leaveStage",s)},e.handleEnter=function(i){var o=$e(i);a.emit("enterStage",{event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}})};var r=function(o){return function(s){var l=$e(s),u={event:l,preventSigmaDefault:function(){return l.preventSigmaDefault()}},d=Ea(a,l,o);if(d){a.emit(Mt(d.kind,o),Bt(d,u));return}a.emit("".concat(o,"Stage"),u)}};e.handleClick=r("click"),e.handleRightClick=r("rightClick"),e.handleDoubleClick=r("doubleClick"),e.handleWheel=r("wheel"),e.handleDown=function(i){var o=$e(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}},l=Ea(a,o,"down");if(l){l.kind==="node"&&a.settings.enableNodeDrag&&(a.dragManager.pendingNode=l.key),a.emit(Mt(l.kind,"down"),Bt(l,s));return}a.emit("downStage",s)},e.handleUp=function(i){var o=$e(i),s={event:o,preventSigmaDefault:function(){return o.preventSigmaDefault()}},l=a.dragManager.end();l&&a.emit("nodeDragEnd",B({node:l.node,allDraggedNodes:l.allNodes},s));var u=Ea(a,o,"up");if(u){a.emit(Mt(u.kind,"up"),Bt(u,s));return}a.emit("upStage",s)},n.on("mousemove",e.handleMove),n.on("mousemovebody",e.handleMoveBody),n.on("click",e.handleClick),n.on("rightClick",e.handleRightClick),n.on("doubleClick",e.handleDoubleClick),n.on("wheel",e.handleWheel),n.on("mousedown",e.handleDown),n.on("mouseup",e.handleUp),n.on("mouseleave",e.handleLeave),n.on("mouseenter",e.handleEnter),t.on("touchdown",e.handleDown),t.on("touchdown",e.handleMove),t.on("touchup",e.handleUp),t.on("touchmove",e.handleMove),t.on("tap",e.handleClick),t.on("doubletap",e.handleDoubleClick),t.on("touchmove",e.handleMoveBody)}function bd(a,n){var t=a.graph,e=new Set(["x","y","zIndex","type"]);n.eachNodeAttributesUpdatedGraphUpdate=function(r){var i,o=(i=r.hints)===null||i===void 0?void 0:i.attributes,s=!o||o.some(function(l){return e.has(l)});a.refresh({partialGraph:{nodes:t.nodes()},skipIndexation:!s,schedule:!0})},n.eachEdgeAttributesUpdatedGraphUpdate=function(r){var i,o=(i=r.hints)===null||i===void 0?void 0:i.attributes,s=o&&["zIndex","type"].some(function(l){return o?.includes(l)});a.refresh({partialGraph:{edges:t.edges()},skipIndexation:!s,schedule:!0})},n.addNodeGraphUpdate=function(r){a.refresh({partialGraph:{nodes:[r.key]},skipIndexation:!1,schedule:!0})},n.updateNodeGraphUpdate=function(r){a.refresh({partialGraph:{nodes:[r.key]},skipIndexation:!1,schedule:!0})},n.dropNodeGraphUpdate=function(r){a.removeNode(r.key),a.scheduleProcess()},n.addEdgeGraphUpdate=function(r){var i=r.key;a.markNodesDirty([r.source,r.target]),a.edgeGroups.register(i);var o=a.edgeGroups.getSiblings(i);a.refresh({partialGraph:{edges:[i].concat($(o))},schedule:!0})},n.updateEdgeGraphUpdate=function(r){a.refresh({partialGraph:{edges:[r.key]},skipIndexation:!1,schedule:!0})},n.dropEdgeGraphUpdate=function(r){var i=r.key;a.markNodesDirty([r.source,r.target]);var o=a.edgeGroups.getSiblings(i);a.edgeGroups.unregister(i),a.removeEdge(i);var s=M(o),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;a.addEdge(u)}}catch(d){s.e(d)}finally{s.f()}a.scheduleProcess()},n.clearEdgesGraphUpdate=function(){a.clearEdgeState(),a.clearEdgeIndices(),a.refresh({schedule:!0})},n.clearGraphUpdate=function(){a.clearEdgeState(),a.clearNodeState(),a.clearEdgeIndices(),a.clearNodeIndices(),a.refresh({schedule:!0})},t.on("nodeAdded",n.addNodeGraphUpdate),t.on("nodeDropped",n.dropNodeGraphUpdate),t.on("nodeAttributesUpdated",n.updateNodeGraphUpdate),t.on("eachNodeAttributesUpdated",n.eachNodeAttributesUpdatedGraphUpdate),t.on("edgeAdded",n.addEdgeGraphUpdate),t.on("edgeDropped",n.dropEdgeGraphUpdate),t.on("edgeAttributesUpdated",n.updateEdgeGraphUpdate),t.on("eachEdgeAttributesUpdated",n.eachEdgeAttributesUpdatedGraphUpdate),t.on("edgesCleared",n.clearEdgesGraphUpdate),t.on("cleared",n.clearGraphUpdate)}function yd(a,n){a.removeListener("nodeAdded",n.addNodeGraphUpdate),a.removeListener("nodeDropped",n.dropNodeGraphUpdate),a.removeListener("nodeAttributesUpdated",n.updateNodeGraphUpdate),a.removeListener("eachNodeAttributesUpdated",n.eachNodeAttributesUpdatedGraphUpdate),a.removeListener("edgeAdded",n.addEdgeGraphUpdate),a.removeListener("edgeDropped",n.dropEdgeGraphUpdate),a.removeListener("edgeAttributesUpdated",n.updateEdgeGraphUpdate),a.removeListener("eachEdgeAttributesUpdated",n.eachEdgeAttributesUpdatedGraphUpdate),a.removeListener("edgesCleared",n.clearEdgesGraphUpdate),a.removeListener("cleared",n.clearGraphUpdate)}var xd={x:.5,y:.5,angle:0,ratio:1},_d=8,Td=.001;function Sd(a){var n=a.coords,t=a.nodeData,e=a.dimensions,r=a.stagePadding,i=a.zoomToSizeRatioFunction,o=a.itemSizesReference,s=a.fitLabels,l=a.nodeLabelBox,u=Object.keys(n);if(!u.length)return a.extent;for(var d=i(1)||1,c=o==="positions",f=e.width,h=e.height,g=a.extent,m=0;m<_d;m++){for(var p=cn(g),v={width:g.x[1]-g.x[0]||1,height:g.y[1]-g.y[0]||1},b=Pe(xd,e,v,r),y=Ci(b,p({x:0,y:0}),f,h),T=Ci(b,p({x:1,y:0}),f,h),x=Math.hypot(T.x-y.x,T.y-y.y)||1,_=1/0,R=-1/0,E=1/0,L=-1/0,D=0,F=u.length;D<F;D++){var A=u[D],I=t[A],w=I.size/d*(c?x:1),k=-w,G=w,N=-w,P=w;if(s){var C=l(I,w);C&&(C.minX<k&&(k=C.minX),C.maxX>G&&(G=C.maxX),C.minY<N&&(N=C.minY),C.maxY>P&&(P=C.maxY))}var z=n[A],H=z.x,U=z.y;_=Math.min(_,H+k/x),R=Math.max(R,H+G/x),E=Math.min(E,U-P/x),L=Math.max(L,U-N/x)}var q={x:[_,R],y:[E,L]},X=Math.max(q.x[1]-q.x[0],q.y[1]-q.y[0])||1,j=Math.max(Math.abs(q.x[0]-g.x[0]),Math.abs(q.x[1]-g.x[1]),Math.abs(q.y[0]-g.y[0]),Math.abs(q.y[1]-g.y[1]));if(g=q,j/X<Td)break}return g}function Ci(a,n,t,e){var r=nt(a,n);return{x:(1+r.x)*t/2,y:(1-r.y)*e/2}}var Ed=typeof navigator<"u"&&/Mac|iP(hone|ad|od)/.test(navigator.platform),Rd=1500,Ad=`.sigma-gesture-hint {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 1em;
  background: #00000066;
  color: #ffffff;
  font-size: 1em;
  pointer-events: none;
  transition: opacity 0.1s;
}`;function Pi(a){var n,t,e=st("style");e.textContent=a,document.head.appendChild(e);var r=((n=(t=e.sheet)===null||t===void 0?void 0:t.cssRules.length)!==null&&n!==void 0?n:0)>0;return e.remove(),r}var Ve=null;function Dd(){return Ve===null&&(Ve=Ad,Pi("@scope {}")&&(Ve=`@scope {
`.concat(Ve,`
}`)),Pi("@layer sigma-gesture-hint {}")&&(Ve=`@layer sigma-gesture-hint {
`.concat(Ve,`
}`))),Ve}var wd=function(){function a(n){Y(this,a),S(this,"hideTimeout",null),this.styleElement=st("style"),this.styleElement.textContent=Dd(),n.appendChild(this.styleElement),this.element=st("div",{opacity:"0"},{class:"sigma-gesture-hint"}),n.appendChild(this.element)}return K(a,[{key:"show",value:function(t,e){var r=this,i=t==="touch"?e.sharedGestureTouchMessage:Ed?e.sharedGestureAppleWheelMessage:e.sharedGestureWheelMessage;i&&(this.element.textContent=i,this.element.style.opacity="1",typeof this.hideTimeout=="number"&&clearTimeout(this.hideTimeout),this.hideTimeout=window.setTimeout(function(){r.hideTimeout=null,r.element.style.opacity="0"},Rd))}},{key:"kill",value:function(){typeof this.hideTimeout=="number"&&clearTimeout(this.hideTimeout),this.styleElement.remove(),this.element.remove()}}])}(),Ld=function(){function a(n){Y(this,a),S(this,"readBuffer",null),S(this,"fence",null),S(this,"result",new Uint8Array(4)),S(this,"generation",0),S(this,"readGeneration",0),S(this,"lastEvent",null),S(this,"active",!1),S(this,"dirty",!1),S(this,"rafId",null),S(this,"killed",!1),this.options=n}return K(a,[{key:"pointerMoved",value:function(t){this.lastEvent=t,this.active=!0,!this.options.isRenderPending()&&this.request()}},{key:"pointerLeft",value:function(){this.active=!1,this.dirty=!1}},{key:"frameRendered",value:function(){this.request()}},{key:"invalidate",value:function(){this.generation++}},{key:"request",value:function(){if(!(this.killed||!this.active||!this.lastEvent)){if(this.fence){this.dirty=!0;return}this.startRead()}}},{key:"startRead",value:function(){var t=this.options,e=t.gl,r=t.getFrameBuffer,i=t.getPixelRatio,o=t.getDownSizingRatio;this.readGeneration=this.generation;var s=this.lastEvent,l=Bn(e,s.x,s.y,i(),o()),u=Q(l,2),d=u[0],c=u[1];this.readBuffer||(this.readBuffer=e.createBuffer()),e.bindFramebuffer(e.FRAMEBUFFER,r()),e.bindBuffer(e.PIXEL_PACK_BUFFER,this.readBuffer),e.bufferData(e.PIXEL_PACK_BUFFER,4,e.STREAM_READ),e.readPixels(d,c,1,1,e.RGBA,e.UNSIGNED_BYTE,0),e.bindBuffer(e.PIXEL_PACK_BUFFER,null),e.bindFramebuffer(e.FRAMEBUFFER,null),this.fence=e.fenceSync(e.SYNC_GPU_COMMANDS_COMPLETE,0),e.flush(),this.schedulePoll(s)}},{key:"schedulePoll",value:function(t){var e=this;this.rafId=requestAnimationFrame(function(){e.rafId=null,e.poll(t)})}},{key:"poll",value:function(t){var e=this.options,r=e.gl,i=e.onIndex;if(!(this.killed||!this.fence)){var o=r.clientWaitSync(this.fence,0,0);if(o===r.TIMEOUT_EXPIRED){this.schedulePoll(t);return}if(r.deleteSync(this.fence),this.fence=null,o!==r.WAIT_FAILED&&this.readGeneration===this.generation){r.bindBuffer(r.PIXEL_PACK_BUFFER,this.readBuffer),r.getBufferSubData(r.PIXEL_PACK_BUFFER,0,this.result),r.bindBuffer(r.PIXEL_PACK_BUFFER,null);var s=Q(this.result,4),l=s[0],u=s[1],d=s[2],c=s[3];this.active&&i(Wn(l,u,d,c),t)}this.dirty&&(this.dirty=!1,this.active&&this.lastEvent&&!this.options.isRenderPending()&&this.startRead())}}},{key:"reset",value:function(){this.rafId!==null&&cancelAnimationFrame(this.rafId),this.rafId=null,this.fence=null,this.readBuffer=null,this.dirty=!1}},{key:"kill",value:function(){this.killed=!0,this.rafId!==null&&cancelAnimationFrame(this.rafId),this.rafId=null;var t=this.options.gl;this.fence&&t.deleteSync(this.fence),this.fence=null,this.readBuffer&&t.deleteBuffer(this.readBuffer),this.readBuffer=null}}])}(),ki=function(){function a(n,t){Y(this,a),this.key=n,this.size=t}return K(a,null,[{key:"compare",value:function(t,e){return t.size>e.size?-1:t.size<e.size||t.key>e.key?1:-1}}])}(),Ln=function(){function a(){Y(this,a),S(this,"width",0),S(this,"height",0),S(this,"cellSize",0),S(this,"columns",0),S(this,"rows",0),S(this,"cells",{})}return K(a,[{key:"resizeAndClear",value:function(t,e){this.width=t.width,this.height=t.height,this.cellSize=e,this.columns=Math.ceil(t.width/e),this.rows=Math.ceil(t.height/e),this.cells={}}},{key:"getIndex",value:function(t){var e=Math.floor(t.x/this.cellSize),r=Math.floor(t.y/this.cellSize);return r*this.columns+e}},{key:"add",value:function(t,e,r){var i=new ki(t,e),o=this.getIndex(r),s=this.cells[o];s||(s=[],this.cells[o]=s),s.push(i)}},{key:"organize",value:function(){for(var t in this.cells){var e=this.cells[t];e.sort(ki.compare)}}},{key:"getLabelsToDisplay",value:function(t,e,r){var i=this.cellSize*this.cellSize,o=i/t/t,s=o*e/i,l=Math.ceil(s),u=[];if(r)for(var d=Math.max(0,Math.floor(r.x1/this.cellSize)),c=Math.min(this.columns-1,Math.floor(r.x2/this.cellSize)),f=Math.max(0,Math.floor(r.y1/this.cellSize)),h=Math.min(this.rows-1,Math.floor(r.y2/this.cellSize)),g=f;g<=h;g++)for(var m=d;m<=c;m++){var p=g*this.columns+m,v=this.cells[p];if(v)for(var b=0;b<Math.min(l,v.length);b++)u.push(v[b].key)}else for(var y in this.cells)for(var T=this.cells[y],x=0;x<Math.min(l,T.length);x++)u.push(T[x].key);return u}}])}();function Cd(a){var n=a.graph,t=a.hoveredNode,e=a.highlightedNodes,r=a.displayedNodeLabels,i=new Set,o=new Set(e);t&&o.add(t);var s=M(o),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;n.hasNode(u)&&n.forEachEdge(u,function(h){i.add(h)})}}catch(h){s.e(h)}finally{s.f()}var d=M(r),c;try{var f=function(){var g=c.value;if(o.has(g))return 1;n.forEachEdge(g,function(m,p,v,b){var y=v===g?b:v;r.has(y)&&i.add(m)})};for(d.s();!(c=d.n()).done;)f()}catch(h){d.e(h)}finally{d.f()}return Array.from(i)}var vt=150,pt=50,Pd={both:0,node:1,label:2},kd={over:0,above:1,below:2,auto:3},Fi=12,Fd=3,Id=function(){function a(n){Y(this,a),S(this,"labelGrid",new Ln),S(this,"edgeAnchorGrid",new Ln),S(this,"displayedNodeLabels",new Set),S(this,"displayedEdgeLabels",new Set),S(this,"edgeLabelCandidates",[]),S(this,"renderedNodeLabels",new Set),S(this,"labelSizeCache",new Map),S(this,"framePassPoints",new Float32Array(0)),S(this,"labelsDirty",!0),this.internals=n}return K(a,[{key:"resetFrame",value:function(){this.displayedNodeLabels=new Set,this.renderedNodeLabels=new Set,this.labelSizeCache.clear()}},{key:"clearEdgeLabels",value:function(){this.displayedEdgeLabels=new Set}},{key:"resetLabelGrid",value:function(){this.labelGrid=new Ln,this.edgeAnchorGrid=new Ln}},{key:"processWebGLLabels",value:function(t){for(var e,r=this.internals,i=r.labelProgram,o=r.primitives,s=r.nodeDataCache,l=(o==null||(e=o.nodes)===null||e===void 0||(e=e.label)===null||e===void 0||(e=e.font)===null||e===void 0?void 0:e.family)||"sans-serif",u=new Map,d=0,c=t.length;d<c;d++){var f=t[d],h=s[f];if(!(h.visibility==="hidden"||!h.label)){var g=h.labelFont||l,m=u.get(g);m?m.push(h.label):u.set(g,[h.label])}}var p=M(u),v;try{for(p.s();!(v=p.n()).done;){var b=Q(v.value,2),y=b[0],T=b[1],x=gn(y),_=x.family,R=x.weight,E=x.style,L=i.registerFont(_,R,E);i.ensureGlyphsReady(T,L)}}catch(D){p.e(D)}finally{p.f()}}},{key:"measureNodeLabel",value:function(t){var e,r;if(!t.label)return{width:0,height:0,textHeight:0};var i=this.internals,o=i.labelProgram,s=i.primitives,l=(e=t.labelSize)!==null&&e!==void 0?e:14,u=t.labelFont||(s==null||(r=s.nodes)===null||r===void 0||(r=r.label)===null||r===void 0||(r=r.font)===null||r===void 0?void 0:r.family)||"sans-serif",d="".concat(t.label,"|").concat(l,"|").concat(u);if(this.labelSizeCache.has(d))return this.labelSizeCache.get(d);var c=gn(u),f=c.family,h=c.weight,g=c.style,m=o.registerFont(f,h,g),p=o.measureLabel(t.label,l,m);return this.labelSizeCache.set(d,p),p}},{key:"nodeLabelBox",value:function(t,e){var r,i,o,s,l;if(t.visibility==="hidden"||t.labelVisibility==="hidden")return null;var u=this.measureNodeLabel(t),d=u.width,c=u.height,f=u.textHeight;if(!d)return null;var h=(r=(i=this.internals.primitives)===null||i===void 0||(i=i.nodes)===null||i===void 0||(i=i.label)===null||i===void 0?void 0:i.margin)!==null&&r!==void 0?r:dt,g=e+h,m=t.labelBackgroundColor?(o=t.labelBackgroundPadding)!==null&&o!==void 0?o:ha:0,p=d/2,v=c/2,b=p+m,y=v+m,T=f/2,x=0,_=0;switch((s=t.labelPosition)!==null&&s!==void 0?s:"right"){case"left":x=-(g+p);break;case"above":_=-(g+T);break;case"below":_=g+T;break;case"over":break;default:x=g+p}var R=(l=t.labelAngle)!==null&&l!==void 0?l:0,E=Mn({x,y:_},R),L=E.x,D=E.y,F=Math.abs(Math.cos(R)),A=Math.abs(Math.sin(R)),I=F*b+A*y,w=A*b+F*y;return{minX:L-I,maxX:L+I,minY:D-w,maxY:D+w}}},{key:"computeDisplayedNodeLabels",value:function(){var t=this.internals.getCameraState(),e=this.internals.getDimensions(),r=e.width,i=e.height,o=this.internals.viewportToFramedGraph({x:-vt,y:-pt}),s=this.internals.viewportToFramedGraph({x:r+vt,y:-pt}),l=this.internals.viewportToFramedGraph({x:-vt,y:i+pt}),u=this.internals.viewportToFramedGraph({x:r+vt,y:i+pt}),d=Math.min(o.x,s.x,l.x,u.x),c=Math.max(o.x,s.x,l.x,u.x),f=Math.min(o.y,s.y,l.y,u.y),h=Math.max(o.y,s.y,l.y,u.y),g=Pe({x:.5,y:.5,ratio:1,angle:0},{width:r,height:i},this.internals.getGraphDimensions(),this.internals.getStagePadding()),m=function(C){var z=nt(g,C);return{x:(1+z.x)*r/2,y:(1-z.y)*i/2}},p=m({x:d,y:f}),v=m({x:c,y:f}),b=m({x:d,y:h}),y=m({x:c,y:h}),T={x1:Math.min(p.x,v.x,b.x,y.x),y1:Math.min(p.y,v.y,b.y,y.y),x2:Math.max(p.x,v.x,b.x,y.x),y2:Math.max(p.y,v.y,b.y,y.y)},x=this.internals,_=x.settings,R=x.nodeDataCache,E=x.nodesWithForcedLabels,L=this.labelGrid.getLabelsToDisplay(t.ratio,_.labelDensity,T);ta(L,E);for(var D=0,F=L.length;D<F;D++){var A=L[D],I=R[A];if(!this.displayedNodeLabels.has(A)&&!(I.visibility==="hidden"||I.labelVisibility==="hidden")&&I.label&&!(I.x<d||I.x>c||I.y<f||I.y>h)){var w=this.internals.framedGraphToViewport(I),k=w.x,G=w.y,N=this.internals.scaleSize(I.size);!Fe(I)&&N<_.labelRenderedSizeThreshold||k<-vt-N||k>r+vt+N||G<-pt-N||G>i+pt+N||this.displayedNodeLabels.add(A)}}}},{key:"buildFramePassPoints",value:function(){var t=this.internals,e=t.nodeDataCache,r=t.nodeDataTexture;if(!r)return{data:this.framePassPoints,count:0};var i=this.displayedNodeLabels.size*3;this.framePassPoints.length<i&&(this.framePassPoints=new Float32Array(i));var o=this.framePassPoints,s=0,l=M(this.displayedNodeLabels),u;try{for(l.s();!(u=l.n()).done;){var d,c,f=u.value,h=e[f];if(h){var g=r.getIndex(f);g<0||(o[s*3]=g,o[s*3+1]=(d=ut[h.labelPosition||we.labelPosition])!==null&&d!==void 0?d:0,o[s*3+2]=(c=h.labelAngle)!==null&&c!==void 0?c:0,s++)}}}catch(m){l.e(m)}finally{l.f()}return{data:o,count:s}}},{key:"renderWebGLLabels",value:function(t,e){var r=this.internals,i=r.nodeDataCache,o=r.labelProgram,s=r.primitives,l=r.nodeDataTexture,u=[],d=M(this.displayedNodeLabels),c;try{for(d.s();!(c=d.n()).done;){var f=c.value;if(!this.renderedNodeLabels.has(f)){var h=i[f];e&&h.labelDepth!==e||(this.renderedNodeLabels.add(f),u.push(f))}}}catch(le){d.e(le)}finally{d.f()}if(u.length!==0){if(this.labelsDirty){for(var g,m,p,v=0,b=0,y=u.length;b<y;b++){var T=i[u[b]];v+=T.label.length}o.reallocate(v);for(var x=14,_=(g=s==null||(m=s.nodes)===null||m===void 0||(m=m.label)===null||m===void 0?void 0:m.margin)!==null&&g!==void 0?g:dt,R=we.labelPosition,E=(s==null||(p=s.nodes)===null||p===void 0||(p=p.label)===null||p===void 0||(p=p.font)===null||p===void 0?void 0:p.family)||"sans-serif",L=new Map,D=0,F=0,A=u.length;F<A;F++){var I,w,k,G,N=u[F],P=i[N],C=P.labelFont||E,z=L.get(C);if(z===void 0){var H=gn(C),U=H.family,q=H.weight,X=H.style;z=o.registerFont(U,q,X),L.set(C,z)}var j={text:P.label,x:P.x,y:P.y,size:(I=P.labelSize)!==null&&I!==void 0?I:x,color:P.labelColor,nodeSize:P.size,margin:_,position:(w=P.labelPosition)!==null&&w!==void 0?w:R,hidden:!1,forceLabel:Fe(P),type:"default",zIndex:(k=P.zIndex)!==null&&k!==void 0?k:0,parentType:"node",parentKey:N,fontKey:z,labelAngle:(G=P.labelAngle)!==null&&G!==void 0?G:0,nodeIndex:l.getIndex(N)},be=o.processLabel(N,D,j);D+=be}o.invalidateBuffers()}o.render(t)}}},{key:"renderBackdrops",value:function(t,e){var r=this.internals,i=r.backdropProgram,o=r.nodeDataCache,s=r.nodesWithBackdrop,l=r.attachmentManager,u=r.pixelRatio,d=r.nodeDataTexture,c=[],f=M(s),h;try{for(f.s();!(h=f.n()).done;){var g,m=h.value,p=o[m];if(!(!p||p.visibility==="hidden")&&!(e&&p.depth!==e)){var v=(g=d?.getIndex(m))!==null&&g!==void 0?g:-1;v<0||c.push({key:m,nodeIndex:v})}}}catch(ze){f.e(ze)}finally{f.f()}if(c.length!==0){i.reallocate(c.length);for(var b=0;b<c.length;b++){var y,T,x,_,R,E,L,D,F=c[b],A=F.key,I=F.nodeIndex,w=o[A],k=this.displayedNodeLabels.has(A),G=k?this.measureNodeLabel(w):{width:0,height:0,textHeight:0},N=G.textHeight,P=G.width,C=G.height,z=0,H=0;if(k&&w.labelAttachment&&l){var U=l.getEntry(A,w.labelAttachment);if(U){var q=w.labelAttachmentPlacement||"below";if(q==="below"||q==="above"){var X=U.height/u;C+=X+Ge,P=Math.max(P,U.width/u),H=q==="below"?(X+Ge)/2:-(X+Ge)/2}else{var j=U.width/u;P+=j+Ge,C=Math.max(C,U.height/u),z=q==="right"?(j+Ge)/2:-(j+Ge)/2}}}var be=w.backdropColor?ke(w.backdropColor):[255,255,255,255],le=w.backdropShadowColor?ke(w.backdropShadowColor):[0,0,0,128],Re=be.map(function(ze){return ze/255}),qe=le.map(function(ze){return ze/255}),mt=(y=w.backdropShadowBlur)!==null&&y!==void 0?y:12,bt=(T=w.backdropPadding)!==null&&T!==void 0?T:6,yt=w.backdropBorderColor?ke(w.backdropBorderColor):[0,0,0,0],$i=yt.map(function(ze){return ze/255}),Vi=(x=w.backdropBorderWidth)!==null&&x!==void 0?x:0,Xi=(_=w.backdropCornerRadius)!==null&&_!==void 0?_:0,Ra=(R=w.backdropLabelPadding)!==null&&R!==void 0?R:-1,ji=Ra<0?bt:Ra,qi=(E=Pd[(L=w.backdropArea)!==null&&L!==void 0?L:"both"])!==null&&E!==void 0?E:0,Yi={key:A,nodeIndex:I,label:w.label,labelWidth:P,labelHeight:C,textHeight:N,type:"default",position:w.labelPosition||we.labelPosition,labelAngle:(D=w.labelAngle)!==null&&D!==void 0?D:0,backdropColor:Re,backdropShadowColor:qe,backdropShadowBlur:mt,backdropPadding:bt,backdropBorderColor:$i,backdropBorderWidth:Vi,backdropCornerRadius:Xi,backdropLabelPadding:ji,backdropArea:qi,labelBoxOffset:[z,H]};i.processBackdrop(b,Yi)}i.invalidateBuffers(),i.render(t)}}},{key:"renderLabelBackgrounds",value:function(t,e){var r=this.internals,i=r.labelBackgroundProgram,o=r.nodeDataCache,s=r.nodeDataTexture,l=se.nodeLabel.writesPickingThisFrame(this.internals),u=[],d=M(this.displayedNodeLabels),c;try{for(d.s();!(c=d.n()).done;){var f=c.value,h=o[f];!h||h.visibility==="hidden"||e&&h.labelDepth!==e||!l&&!h.labelBackgroundColor||u.push(f)}}catch(I){d.e(I)}finally{d.f()}if(u.length!==0){i.reallocate(u.length);for(var g=0;g<u.length;g++){var m,p,v,b,y=u[g],T=o[y],x=(m=s?.getIndex(y))!==null&&m!==void 0?m:-1;if(!(x<0)){var _=this.measureNodeLabel(T),R=_.width,E=_.height,L=_.textHeight,D=Xe(this.internals.pickingState,"nodeLabel",y)||Xe(this.internals.pickingState,"node",y),F=T.labelBackgroundColor?ve(T.labelBackgroundColor):ve("transparent"),A={nodeIndex:x,id:at(D),color:F,labelWidth:R,labelHeight:E,textHeight:L,positionMode:(p=ut[T.labelPosition||we.labelPosition])!==null&&p!==void 0?p:0,labelAngle:(v=T.labelAngle)!==null&&v!==void 0?v:0,padding:(b=T.labelBackgroundPadding)!==null&&b!==void 0?b:ha};i.processLabelBackground(g,A)}}i.invalidateBuffers(),i.render(t)}}},{key:"cacheAttachments",value:function(t){var e=this.internals,r=e.attachmentManager,i=e.pixelRatio,o=e.nodeDataCache,s=e.nodesWithBackdrop,l=e.graph;if(r){var u=M(s),d;try{for(u.s();!(d=u.n()).done;){var c=d.value;if(this.displayedNodeLabels.has(c)){var f=o[c];if(!(!f||f.visibility==="hidden")&&!(t&&f.depth!==t)&&f.labelAttachment){var h=l.getNodeAttributes(c),g=this.measureNodeLabel(f),m=g.width,p=g.height,v={node:c,attributes:h,pixelRatio:i,labelWidth:m,labelHeight:p};r.renderAttachment(c,f.labelAttachment,v)}}}}catch(b){u.e(b)}finally{u.f()}r.regenerateAtlas()}}},{key:"renderAttachments",value:function(t,e){var r=this.internals,i=r.attachmentManager,o=r.attachmentProgram,s=r.nodeDataCache,l=r.nodesWithBackdrop,u=r.pixelRatio,d=r.nodeDataTexture;if(!(!i||!o)){var c=0;o.reallocateAttachments(l.size);var f=M(l),h;try{for(f.s();!(h=f.n()).done;){var g,m,p,v,b=h.value;if(this.displayedNodeLabels.has(b)){var y=s[b];if(!(!y||y.visibility==="hidden")&&!(e&&y.labelDepth!==e)&&y.labelAttachment){var T=i.getEntry(b,y.labelAttachment);if(T){var x=(g=d?.getIndex(b))!==null&&g!==void 0?g:-1;if(!(x<0)){var _=this.measureNodeLabel(y),R=_.width,E=_.height,L=_.textHeight,D=(m=Kr[y.labelAttachmentPlacement||"below"])!==null&&m!==void 0?m:0;o.processAttachment(c,{nodeIndex:x,atlasX:T.x,atlasY:T.y,atlasW:T.width,atlasH:T.height,attachWidth:T.width/u,attachHeight:T.height/u,positionMode:(p=ut[y.labelPosition||we.labelPosition])!==null&&p!==void 0?p:0,attachmentPlacement:D,labelWidth:R,labelHeight:E,textHeight:L,labelAngle:(v=y.labelAngle)!==null&&v!==void 0?v:0}),c++}}}}}}catch(F){f.e(F)}finally{f.f()}c!==0&&(o.reallocateAttachments(c),i.bindTexture(It),o.invalidateBuffers(),o.render(t))}}},{key:"computeDisplayedEdgeLabels",value:function(){var t=this.internals,e=t.graph,r=t.stateManager,i=t.settings,o=t.edgesWithForcedLabels,s=r.getHighlightedNodes(),l=i.edgeLabelAnchors==="allNodes"?new Set(this.edgeAnchorGrid.getLabelsToDisplay(this.internals.getCameraState().ratio,i.labelDensity)):this.displayedNodeLabels,u=r.hovered,d=Cd({graph:e,hoveredNode:u?.kind==="node"?u.key:null,displayedNodeLabels:l,highlightedNodes:s});ta(d,o),this.edgeLabelCandidates=d,this.displayedEdgeLabels=new Set}},{key:"filterEdgeLabelsForDepth",value:function(t){for(var e=this.internals,r=e.graph,i=e.nodeDataCache,o=e.edgeDataCache,s=[],l=new Set,u=0,d=this.edgeLabelCandidates.length;u<d;u++){var c=this.edgeLabelCandidates[u];if(!l.has(c)){l.add(c);var f=r.extremities(c),h=i[f[0]],g=i[f[1]],m=o[c];!m||!h||!g||m.visibility==="hidden"||m.labelVisibility==="hidden"||h.visibility==="hidden"||g.visibility==="hidden"||t&&m.labelDepth!==t||m.label&&s.push(c)}}return s}},{key:"renderEdgeLabels",value:function(t,e){var r=this.internals,i=r.graph,o=r.nodeDataCache,s=r.edgeDataCache,l=r.primitives,u=r.edgeLabelProgram,d=r.nodeDataTexture,c=r.edgeDataTexture;if(u){var f=this.filterEdgeLabelsForDepth(e),h=M(f),g;try{for(h.s();!(g=h.n()).done;){var m=g.value;this.displayedEdgeLabels.add(m)}}catch(j){h.e(j)}finally{h.f()}if(f.length!==0){if(this.labelsDirty){var p,v,b=0,y=M(f),T;try{for(y.s();!(T=y.n()).done;){var x=T.value;b+=s[x].label.length}}catch(j){y.e(j)}finally{y.f()}u.reallocate(b);var _=(p=l==null||(v=l.edges)===null||v===void 0||(v=v.label)===null||v===void 0?void 0:v.margin)!==null&&p!==void 0?p:5,R="over",E=0,L=M(f),D;try{for(L.s();!(D=L.n()).done;){var F,A,I=D.value,w=i.extremities(I),k=w[0],G=w[1],N=o[k],P=o[G],C=s[I],z=d.getIndex(k),H=d.getIndex(G),U=c.getIndex(I),q={text:C.label,x:(N.x+P.x)/2,y:(N.y+P.y)/2,size:Fi,color:C.labelColor,nodeSize:0,nodeIndex:-1,margin:_,position:(F=C.labelPosition)!==null&&F!==void 0?F:R,hidden:!1,forceLabel:Fe(C),type:"default",zIndex:(A=C.zIndex)!==null&&A!==void 0?A:0,parentType:"edge",parentKey:I,fontKey:"",labelAngle:0,sourceX:N.x,sourceY:N.y,targetX:P.x,targetY:P.y,sourceSize:N.size,targetSize:P.size,sourceShape:N.shape||"circle",targetShape:P.shape||"circle",edgeSize:C.size,offset:0,edgeAttributes:C,sourceNodeIndex:z,targetNodeIndex:H,edgeIndex:U},X=u.processEdgeLabel(I,E,q);E+=X}}catch(j){L.e(j)}finally{L.f()}u.invalidateBuffers()}u.render(t)}}}},{key:"renderEdgeLabelBackgrounds",value:function(t,e){var r,i,o=this.internals,s=o.edgeLabelBackgroundProgram,l=o.edgeLabelProgram,u=o.edgeDataCache,d=o.primitives,c=o.edgeDataTexture;if(!(!c||!l||!s)){var f=se.edgeLabel.writesPickingThisFrame(this.internals),h=(r=d==null||(i=d.edges)===null||i===void 0||(i=i.label)===null||i===void 0?void 0:i.margin)!==null&&r!==void 0?r:5,g="over",m=this.filterEdgeLabelsForDepth(e),p=[],v=M(m),b;try{for(v.s();!(b=v.n()).done;){var y=b.value;!f&&!u[y].labelBackgroundColor||p.push(y)}}catch(N){v.e(N)}finally{v.f()}if(p.length!==0){s.reallocate(p.length);for(var T=0;T<p.length;T++){var x,_,R,E=p[T],L=u[E],D=L.label,F=l.measureLabelAtlasWidth(D),A=(x=L.labelPosition)!==null&&x!==void 0?x:g,I=typeof A=="string"&&(_=kd[A])!==null&&_!==void 0?_:0,w=Xe(this.internals.pickingState,"edgeLabel",E)||Xe(this.internals.pickingState,"edge",E),k=L.labelBackgroundColor?ve(L.labelBackgroundColor):ve("transparent"),G={edgeIndex:c.getIndex(E),baseFontSize:Fi,totalTextWidth:F,positionMode:I,margin:h,padding:(R=L.labelBackgroundPadding)!==null&&R!==void 0?R:Fd,color:k,id:at(w),edgeAttributes:L};s.processEdgeLabelBackground(T,E,G)}s.invalidateBuffers(),s.render(t)}}}}])}(),Nd=function(){function a(n,t,e,r){Y(this,a),S(this,"nodeStates",new Map),S(this,"edgeStates",new Map),S(this,"hovered",null),S(this,"dirtyNodes",new Set),S(this,"dirtyEdges",new Set),S(this,"graphStateChanged",!1),S(this,"graphStateFlagsDirty",!1),this.scheduleRefresh=n,this.customNodeStateDefaults=t,this.customEdgeStateDefaults=e,this.customGraphStateDefaults=r,this.graphState=qn(r)}return K(a,[{key:"getNodeState",value:function(t){t=""+t;var e=this.nodeStates.get(t);return e||(e=xr(this.customNodeStateDefaults),this.nodeStates.set(t,e)),e}},{key:"getEdgeState",value:function(t){t=""+t;var e=this.edgeStates.get(t);return e||(e=_r(this.customEdgeStateDefaults),this.edgeStates.set(t,e)),e}},{key:"getGraphState",value:function(){return this.flushGraphStateFlags(),this.graphState}},{key:"getHighlightedNodes",value:function(){var t=new Set,e=M(this.nodeStates),r;try{for(e.s();!(r=e.n()).done;){var i=Q(r.value,2),o=i[0],s=i[1];s.isHighlighted&&t.add(o)}}catch(l){e.e(l)}finally{e.f()}return t}},{key:"setNodeState",value:function(t,e){t=""+t;var r=this.getNodeState(t);if(ot(r,e)){var i=B(B({},r),e);this.nodeStates.set(t,i),this.dirtyNodes.add(t),this.updateHoveredNodeTracking(t,r,i),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}}},{key:"setEdgeState",value:function(t,e){t=""+t;var r=this.getEdgeState(t);if(ot(r,e)){var i=B(B({},r),e);this.edgeStates.set(t,i),this.dirtyEdges.add(t),this.updateHoveredEdgeTracking(t,r,i),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}}},{key:"setGraphState",value:function(t){if(ot(this.graphState,t)){var e=B(B({},this.graphState),t);e.isIdle=!e.isPanning&&!e.isZooming&&!e.isDragging,this.graphState=e,this.graphStateChanged=!0,this.scheduleRefresh()}}},{key:"setNodesState",value:function(t,e){var r=!1,i=M(t),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;s=""+s;var l=this.getNodeState(s);if(ot(l,e)){var u=B(B({},l),e);this.nodeStates.set(s,u),this.dirtyNodes.add(s),this.updateHoveredNodeTracking(s,l,u),r=!0}}}catch(d){i.e(d)}finally{i.f()}r&&(this.graphStateFlagsDirty=!0,this.scheduleRefresh())}},{key:"setEdgesState",value:function(t,e){var r=!1,i=M(t),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;s=""+s;var l=this.getEdgeState(s);if(ot(l,e)){var u=B(B({},l),e);this.edgeStates.set(s,u),this.dirtyEdges.add(s),this.updateHoveredEdgeTracking(s,l,u),r=!0}}}catch(d){i.e(d)}finally{i.f()}r&&(this.graphStateFlagsDirty=!0,this.scheduleRefresh())}},{key:"markNodesDirty",value:function(t){var e=M(t),r;try{for(e.s();!(r=e.n()).done;){var i=r.value;this.dirtyNodes.add(i)}}catch(o){e.e(o)}finally{e.f()}this.scheduleRefresh()}},{key:"removeNode",value:function(t){this.nodeStates.delete(t),this.dirtyNodes.delete(t),this.clearHoveredFor("node",t),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}},{key:"removeEdge",value:function(t){this.edgeStates.delete(t),this.dirtyEdges.delete(t),this.clearHoveredFor("edge",t),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}},{key:"pruneNodes",value:function(t){var e=M(this.nodeStates.keys()),r;try{for(e.s();!(r=e.n()).done;){var i=r.value;t(i)||this.removeNode(i)}}catch(o){e.e(o)}finally{e.f()}}},{key:"pruneEdges",value:function(t){var e=M(this.edgeStates.keys()),r;try{for(e.s();!(r=e.n()).done;){var i=r.value;t(i)||this.removeEdge(i)}}catch(o){e.e(o)}finally{e.f()}}},{key:"clearNodes",value:function(){this.nodeStates.clear(),this.dirtyNodes.clear(),this.clearHoveredForKinds(Pn("node")),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}},{key:"clearEdges",value:function(){this.edgeStates.clear(),this.dirtyEdges.clear(),this.clearHoveredForKinds(Pn("edge")),this.graphStateFlagsDirty=!0,this.scheduleRefresh()}},{key:"resetGraphState",value:function(){this.graphState=qn(this.customGraphStateDefaults),this.graphStateChanged=!1,this.graphStateFlagsDirty=!1}},{key:"clearDirtyTracking",value:function(){this.dirtyNodes.clear(),this.dirtyEdges.clear(),this.graphStateChanged=!1}},{key:"setHovered",value:function(t){this.hovered=t}},{key:"clearHoveredFor",value:function(t,e){this.hovered&&this.hovered.key===e&&Pn(t).includes(this.hovered.kind)&&(this.hovered=null)}},{key:"clearHoveredForKinds",value:function(t){this.hovered&&t.includes(this.hovered.kind)&&(this.hovered=null)}},{key:"updateGraphStateFromNodes",value:function(){var t,e=!1,r=!1,i=!1,o=M(this.nodeStates),s;try{for(o.s();!(s=o.n()).done;){var l=Q(s.value,2),u=l[1];if(u.isHovered&&(e=!0),u.isHighlighted&&(r=!0),u.isDragged&&(i=!0),e&&r&&i)break}}catch(c){o.e(c)}finally{o.f()}!e&&((t=this.hovered)===null||t===void 0?void 0:t.kind)==="edge"&&(e=!0);var d=!this.graphState.isPanning&&!this.graphState.isZooming&&!i;(this.graphState.hasHovered!==e||this.graphState.hasHighlighted!==r||this.graphState.isDragging!==i||this.graphState.isIdle!==d)&&(this.graphStateChanged=!0),this.graphState=B(B({},this.graphState),{},{hasHovered:e,hasHighlighted:r,isDragging:i,isIdle:d})}},{key:"updateGraphStateFromEdges",value:function(){var t,e=((t=this.hovered)===null||t===void 0?void 0:t.kind)==="node";if(!e){var r=M(this.edgeStates),i;try{for(r.s();!(i=r.n()).done;){var o=Q(i.value,2),s=o[1];if(s.isHovered){e=!0;break}}}catch(l){r.e(l)}finally{r.f()}}this.graphState.hasHovered!==e&&(this.graphStateChanged=!0),this.graphState=B(B({},this.graphState),{},{hasHovered:e})}},{key:"flushGraphStateFlags",value:function(){this.graphStateFlagsDirty&&(this.updateGraphStateFromNodes(),this.updateGraphStateFromEdges(),this.graphStateFlagsDirty=!1)}},{key:"updateHoveredNodeTracking",value:function(t,e,r){var i;if(e.isHovered!==r.isHovered)if(r.isHovered){var o;if(((o=this.hovered)===null||o===void 0?void 0:o.kind)==="node"&&this.hovered.key!==t){var s=this.hovered.key,l=this.getNodeState(s);this.nodeStates.set(s,B(B({},l),{},{isHovered:!1})),this.dirtyNodes.add(s)}this.hovered={kind:"node",key:t}}else((i=this.hovered)===null||i===void 0?void 0:i.kind)==="node"&&this.hovered.key===t&&(this.hovered=null)}},{key:"updateHoveredEdgeTracking",value:function(t,e,r){var i;if(e.isHovered!==r.isHovered)if(r.isHovered){var o;if(((o=this.hovered)===null||o===void 0?void 0:o.kind)==="edge"&&this.hovered.key!==t){var s=this.hovered.key,l=this.getEdgeState(s);this.edgeStates.set(s,B(B({},l),{},{isHovered:!1})),this.dirtyEdges.add(s)}this.hovered={kind:"edge",key:t}}else((i=this.hovered)===null||i===void 0?void 0:i.kind)==="edge"&&this.hovered.key===t&&(this.hovered=null)}}])}(),Ii=1,Ni=2,Gi=3,zi=4,Gd=function(a){function n(t,e){var r,i,o,s,l,u=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};Y(this,n),l=te(this,n),S(l,"nodeReducer",null),S(l,"edgeReducer",null),S(l,"stageCanvas",null),S(l,"mouseLayer",null),S(l,"gestureHint",null),S(l,"extraElements",{}),S(l,"webGLContext",null),S(l,"pickingFrameBuffer",null),S(l,"pickingTexture",null),S(l,"pickingDepthBuffer",null),S(l,"activeListeners",{}),S(l,"nodeVariableEntries",[]),S(l,"edgeVariableEntries",[]),S(l,"edgePathsByName",new Map),S(l,"nodeProgramIndex",{}),S(l,"edgeProgramIndex",{}),S(l,"edgeTextureIndexCache",{}),S(l,"nodeGraphCoords",{}),S(l,"nodeExtent",{x:[0,1],y:[0,1]}),S(l,"matrix",ge()),S(l,"invMatrix",ge()),S(l,"correctionRatio",1),S(l,"frameId",0),S(l,"customBBox",null),S(l,"gpuTimerExt",void 0),S(l,"activeGpuTimerQuery",null),S(l,"pendingGpuTimerQueries",[]),S(l,"normalizationFunction",cn({x:[0,1],y:[0,1]})),S(l,"graphToViewportRatio",1),S(l,"pickingState",dd()),S(l,"prevNodeVisibilities",{}),S(l,"width",0),S(l,"height",0),S(l,"autoRescaleFrozen",!1),S(l,"stylesDeclaration",null),S(l,"resolvedStageStyle",{}),S(l,"renderFrame",null),S(l,"contextLost",!1),S(l,"pendingProcess","full"),S(l,"needToRefreshState",!1),S(l,"checkEdgesEventsFrame",null),S(l,"edgeStyleAnalysis",{dependency:"static",xAttribute:null,yAttribute:null}),S(l,"depthLayers",$(an)),S(l,"customLayerPrograms",new Map),S(l,"nodeShapeSlug",null),S(l,"sdfAtlas",null),S(l,"depthRanges",{nodes:{},edges:{}}),S(l,"nodeBaseDepth",{}),S(l,"edgeBaseDepth",{});var d=u.primitives,c=u.styles,f=u.settings,h=f===void 0?{}:f,g=u.nodeReducer,m=u.edgeReducer,p=u.customNodeState,v=u.customEdgeState,b=u.customGraphState;l.stateManager=new Nd(function(){return l.scheduleStateRefresh()},p,v,b);var y=d??Er;l.stylesDeclaration=c?{nodes:(r=c.nodes)!==null&&r!==void 0?r:sn.nodes,edges:(i=c.edges)!==null&&i!==void 0?i:sn.edges,stage:c.stage}:sn,l.nodeReducer=g??null,l.edgeReducer=m??null;var T=Yn(l.stylesDeclaration.nodes);l.nodeReducer&&(T.dependency="graph-state"),l.edgeStyleAnalysis=Yn(l.stylesDeclaration.edges),l.edgeReducer&&(l.edgeStyleAnalysis.dependency="graph-state"),l.stylesDeclaration.stage&&(l.resolvedStageStyle=ea(l.stylesDeclaration.stage,l.stateManager.graphState));var x=Pr(h);if(fn(x),x.enableNodeDrag){var _=T.xAttribute,R=T.yAttribute;if((!_||!R)&&!x.dragPositionToAttributes)throw new Error('Sigma: `enableNodeDrag` is true but position attribute names could not be inferred from styles. Either use attribute bindings for x/y in your node styles (e.g. `x: { attribute: "x" }`), or provide a `dragPositionToAttributes` setting.')}if(Cr(t),!(e instanceof HTMLElement))throw new Error("Sigma: container should be an html element.");l.container=e,l.edgeGroups=new ud(t,function(P,C){for(var z=0;z<P.length;z++){var H=l.stateManager.getEdgeState(P[z]);H.parallelIndex=z,H.parallelCount=C}});var E=new ld(t,l.viewportToGraph.bind(l),l.setNodesState.bind(l),function(P,C){return l.emit(P,C)});if(l.depthLayers=(o=y.depthLayers)!==null&&o!==void 0?o:$(an),!(c!=null&&c.nodes)&&!tn.every(function(P){return l.depthLayers.includes(P)}))throw new Error("Sigma: depthLayers must include ".concat(tn.join(", ")," for the built-in node styles."));if(!(c!=null&&c.edges)&&!nn.every(function(P){return l.depthLayers.includes(P)}))throw new Error("Sigma: depthLayers must include ".concat(nn.join(", ")," for the built-in edge styles."));l.itemBuckets={nodes:new _a(l.depthLayers),edges:new _a(l.depthLayers)},l.initWebGLContext(),l.mouseLayer=st("div",{position:"absolute",touchAction:"none",userSelect:"none"},{class:"sigma-mouse"}),l.container.appendChild(l.mouseLayer),l.resolvedStageStyle.background&&(l.container.style.backgroundColor=l.resolvedStageStyle.background),l.resolvedStageStyle.cursor&&(l.container.style.cursor=l.resolvedStageStyle.cursor);var L=new bi(l.webGLContext),D=new Ta(l.webGLContext,{channels:1}),F=new yi(l.webGLContext),A=new Ta(l.webGLContext,{channels:4}),I=l.webGLContext,w=new Ld({gl:I,getFrameBuffer:function(){return l.pickingFrameBuffer},getPixelRatio:function(){return l.internals.pixelRatio},getDownSizingRatio:function(){return l.internals.settings.pickingDownSizingRatio},isRenderPending:function(){return l.renderFrame!==null},onIndex:function(C,z){var H;return Oi(l.internals,(H=l.pickingState.lookup[C])!==null&&H!==void 0?H:null,z)}}),k=l.initPrograms(y,x),G=y==null||(s=y.nodes)===null||s===void 0?void 0:s.labelAttachments,N=null;return G&&Object.keys(G).length>0&&(N=new mi(I,G,function(){return l.scheduleRender()})),l.internals=B(B({nodeDataCache:{},edgeDataCache:{},nodesWithForcedLabels:new Set,nodesWithBackdrop:new Set,edgesWithForcedLabels:new Set,settings:x,primitives:y,pixelRatio:Dt(),graph:t,stateManager:l.stateManager,dragManager:E,hoverResolver:w,nodeStyleAnalysis:T,pickingState:l.pickingState},k),{},{attachmentManager:N,nodeDataTexture:L,nodeFrameTexture:D,edgeDataTexture:F,edgeFrameTexture:A,getDimensions:function(){return l.getDimensions()},getGraphDimensions:function(){return l.getGraphDimensions()},getStagePadding:function(){return l.getStagePadding()},getCameraState:function(){return l.camera.getState()},getHitAtPosition:function(C){return l.getHitAtPosition(C)},setNodeState:function(C,z){return l.setNodeState(C,z)},setEdgeState:function(C,z){return l.setEdgeState(C,z)},updateContainerCursor:function(){return l.updateContainerCursor()},scheduleRefresh:function(){return l.scheduleRefresh()},viewportToFramedGraph:function(C){return l.viewportToFramedGraph(C)},viewportToGraph:function(C){return l.viewportToGraph(C)},framedGraphToViewport:function(C){return l.framedGraphToViewport(C)},scaleSize:function(C){return l.scaleSize(C)},emit:function(C,z){return l.emit(C,z)}}),l.labelRenderer=new Id(l.internals),l.resize(),l.initializeWebGLLabels(),l.camera=new Ti,l.bindCameraHandlers(),l.mouseCaptor=new rd(l.mouseLayer,l),l.mouseCaptor.setSettings(l.internals.settings),l.touchCaptor=new sd(l.mouseLayer,l),l.touchCaptor.setSettings(l.internals.settings),l.bindEventHandlers(),l.bindGraphHandlers(),l.handleSettingsUpdate(),l.refresh(),l}return ne(n,a),K(n,[{key:"initializeWebGLLabels",value:function(){this.sdfAtlas=new Oe,this.sdfAtlas.registerFont({family:"sans-serif",weight:"normal",style:"normal"})}},{key:"resetWebGLTexture",value:function(){var e=this.webGLContext;if(!this.pickingFrameBuffer)return this;var r=Math.ceil(this.width*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio),i=Math.ceil(this.height*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio);e.bindFramebuffer(e.FRAMEBUFFER,this.pickingFrameBuffer),this.pickingTexture&&e.deleteTexture(this.pickingTexture);var o=e.createTexture();o&&(e.bindTexture(e.TEXTURE_2D,o),e.texImage2D(e.TEXTURE_2D,0,e.RGBA,r,i,0,e.RGBA,e.UNSIGNED_BYTE,null),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MIN_FILTER,e.NEAREST),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MAG_FILTER,e.NEAREST),e.framebufferTexture2D(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,o,0),this.pickingTexture=o),this.pickingDepthBuffer&&e.deleteRenderbuffer(this.pickingDepthBuffer);var s=e.createRenderbuffer();return s&&(e.bindRenderbuffer(e.RENDERBUFFER,s),e.renderbufferStorage(e.RENDERBUFFER,e.DEPTH_COMPONENT16,r,i),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.DEPTH_ATTACHMENT,e.RENDERBUFFER,s),this.pickingDepthBuffer=s),e.bindFramebuffer(e.FRAMEBUFFER,null),this}},{key:"bindCameraHandlers",value:function(){var e=this;return this.activeListeners.camera=function(){e.refreshMatrices(),e.labelRenderer.labelsDirty=!0,e.scheduleRender()},this.activeListeners.cameraAnimationStart=function(r){var i=r.from,o=r.to;i.ratio!==o.ratio&&e.stateManager.setGraphState({isZooming:!0})},this.activeListeners.cameraAnimationEnd=function(){e.stateManager.setGraphState({isZooming:!1})},this.camera.on("updated",this.activeListeners.camera),this.camera.on("animationStart",this.activeListeners.cameraAnimationStart),this.camera.on("animationEnd",this.activeListeners.cameraAnimationEnd),this}},{key:"unbindCameraHandlers",value:function(){return this.camera.removeListener("updated",this.activeListeners.camera),this.camera.removeListener("animationStart",this.activeListeners.cameraAnimationStart),this.camera.removeListener("animationEnd",this.activeListeners.cameraAnimationEnd),this}},{key:"getHitAtPosition",value:function(e){var r;if(this.contextLost)return null;var i=this.webGLContext;i.bindFramebuffer(i.FRAMEBUFFER,this.pickingFrameBuffer);var o=ar(i,this.pickingFrameBuffer,e.x,e.y,this.internals.pixelRatio,this.internals.settings.pickingDownSizingRatio),s=Wn.apply(void 0,$(o));return(r=this.pickingState.lookup[s])!==null&&r!==void 0?r:null}},{key:"bindEventHandlers",value:function(){return md(this.internals,this.mouseCaptor,this.touchCaptor,this.activeListeners),this}},{key:"bindGraphHandlers",value:function(){var e=this;return bd({graph:this.internals.graph,edgeGroups:this.edgeGroups,updateNode:this.updateNode.bind(this),removeNode:this.removeNode.bind(this),addEdge:this.addEdge.bind(this),updateEdge:this.updateEdge.bind(this),removeEdge:this.removeEdge.bind(this),clearEdgeState:this.clearEdgeState.bind(this),clearNodeState:this.clearNodeState.bind(this),clearEdgeIndices:this.clearEdgeIndices.bind(this),clearNodeIndices:this.clearNodeIndices.bind(this),refresh:this.refresh.bind(this),scheduleProcess:function(){e.pendingProcess="full",e.scheduleRender()},markNodesDirty:function(i){e.internals.nodeStyleAnalysis.dependency==="graph-state"&&e.stateManager.markNodesDirty(i)}},this.activeListeners),this}},{key:"unbindGraphHandlers",value:function(){yd(this.internals.graph,this.activeListeners)}},{key:"getNodeShapeId",value:function(e){return this.internals.nodeShapeMap&&this.internals.nodeGlobalShapeIds&&e.shape&&e.shape in this.internals.nodeShapeMap?this.internals.nodeGlobalShapeIds[this.internals.nodeShapeMap[e.shape]]:kt(e.shape||"circle")}},{key:"processNodes",value:function(){var e=this,r=this.internals.graph,i=this.internals.settings,o=this.getDimensions(),s=i.autoRescale,l=i.autoRescaleContent,u=this.nodeExtent;if(s===!1){var d=o.width,c=o.height;u={x:[-d/2,d/2],y:[-c/2,c/2]}}else(s!=="once"||!this.autoRescaleFrozen)&&(u=this.computeNodeExtent(),l!=="positions"&&!this.customBBox&&(u=Sd({extent:u,coords:this.nodeGraphCoords,nodeData:this.internals.nodeDataCache,dimensions:o,stagePadding:this.getStagePadding(),zoomToSizeRatioFunction:i.zoomToSizeRatioFunction,itemSizesReference:i.itemSizesReference,fitLabels:l==="labels",nodeLabelBox:function(H,U){return e.labelRenderer.nodeLabelBox(H,U)}})),s==="once"&&(this.autoRescaleFrozen=!0));this.nodeExtent=u,this.normalizationFunction=cn(this.customBBox||this.nodeExtent);var f=new Ti,h=Pe(f.getState(),o,this.getGraphDimensions(),this.getStagePadding());this.labelRenderer.labelGrid.resizeAndClear(o,i.labelGridCellSize),this.labelRenderer.edgeAnchorGrid.resizeAndClear(o,i.labelGridCellSize);var g=i.renderEdgeLabels&&i.edgeLabelAnchors==="allNodes",m=!1;wn(this.pickingState,"node");for(var p=r.nodes(),v=0,b=p.length;v<b;v++){var y=p[v],T=this.internals.nodeDataCache[y],x=this.nodeGraphCoords[y];T.x=x.x,T.y=x.y,this.normalizationFunction.applyTo(T),T.visibility!==this.prevNodeVisibilities[y]&&(m=!0),typeof T.label=="string"&&T.visibility!=="hidden"&&T.labelVisibility!=="hidden"&&this.labelRenderer.labelGrid.add(y,T.size,this.framedGraphToViewport(T,{matrix:h})),g&&T.visibility!=="hidden"&&this.labelRenderer.edgeAnchorGrid.add(y,T.size,this.framedGraphToViewport(T,{matrix:h}))}this.labelRenderer.labelGrid.organize(),this.labelRenderer.edgeAnchorGrid.organize(),this.nodeProgram.reallocate(p.length);var _=0;this.depthRanges.nodes={},this.nodeBaseDepth={};var R=this.internals.nodeDataCache,E=M(this.depthLayers),L;try{for(E.s();!(L=E.n()).done;){var D=L.value,F=this.itemBuckets.nodes.getSorted(D,function(z){return R[z].zIndex});if(F.length!==0){this.depthRanges.nodes[D]=[{offset:_,count:F.length}];var A=M(F),I;try{for(A.s();!(I=A.n()).done;){var w=I.value;this.nodeBaseDepth[w]=D,Di(this.pickingState,"node",w),this.addNodeToProgram(w,_++)}}catch(z){A.e(z)}finally{A.f()}}}}catch(z){E.e(z)}finally{E.f()}this.nodeProgram.invalidateBuffers();for(var k=0,G=p.length;k<G;k++)this.prevNodeVisibilities[p[k]]=this.internals.nodeDataCache[p[k]].visibility;this.labelRenderer.processWebGLLabels(p);var N=M(this.customLayerPrograms.values()),P;try{for(N.s();!(P=N.n()).done;){var C=P.value.program;C.cacheData&&C.cacheData()}}catch(z){N.e(z)}finally{N.f()}return m}},{key:"processEdges",value:function(){var e=this.internals.graph,r=e.edges();this.edgeProgram.reallocate(r.length);var i=0;wn(this.pickingState,"edge"),this.depthRanges.edges={},this.edgeBaseDepth={};var o=this.internals.edgeDataCache,s=M(this.depthLayers),l;try{for(s.s();!(l=s.n()).done;){var u=l.value,d=this.itemBuckets.edges.getSorted(u,function(g){return o[g].zIndex});if(d.length!==0){this.depthRanges.edges[u]=[{offset:i,count:d.length}];var c=M(d),f;try{for(c.s();!(f=c.n()).done;){var h=f.value;this.edgeBaseDepth[h]=u,Di(this.pickingState,"edge",h),this.addEdgeToProgram(h,i++)}}catch(g){c.e(g)}finally{c.f()}}}}catch(g){s.e(g)}finally{s.f()}this.edgeProgram.invalidateBuffers()}},{key:"updateNodeDepthRanges",value:function(e,r,i){var o=this.nodeProgramIndex[e];o!==void 0&&(ra(this.depthRanges.nodes,r,o),ia(this.depthRanges.nodes,i,o))}},{key:"updateEdgeDepthRanges",value:function(e,r,i){var o=this.edgeProgramIndex[e];o!==void 0&&(ra(this.depthRanges.edges,r,o),ia(this.depthRanges.edges,i,o))}},{key:"handleSettingsUpdate",value:function(){var e=this,r=this.internals.settings;return this.camera.minRatio=r.minCameraRatio,this.camera.maxRatio=r.maxCameraRatio,this.camera.enabledZooming=r.enableCameraZooming,this.camera.enabledPanning=r.enableCameraPanning,this.camera.enabledRotation=r.enableCameraRotation,r.cameraPanBoundaries?this.camera.constrainState=function(i){return e.cleanCameraState(i,r.cameraPanBoundaries&&Z(r.cameraPanBoundaries)==="object"?r.cameraPanBoundaries:{})}:this.camera.constrainState=null,this.camera.setState(this.camera.getState()),this.mouseLayer.style.touchAction=r.gestureTarget==="graph"?"none":r.gestureTarget==="shared"?"pan-x pan-y":"auto",r.gestureTarget!=="shared"&&this.gestureHint&&(this.gestureHint.kill(),this.gestureHint=null),this.mouseCaptor.setSettings(this.internals.settings),this.touchCaptor.setSettings(this.internals.settings),this}},{key:"cleanCameraState",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=r.tolerance,o=i===void 0?0:i,s=r.boundaries,l=B({},e),u=s||this.nodeExtent,d=Q(u.x,2),c=d[0],f=d[1],h=Q(u.y,2),g=h[0],m=h[1],p=[this.graphToViewport({x:c,y:g},{cameraState:e}),this.graphToViewport({x:f,y:g},{cameraState:e}),this.graphToViewport({x:c,y:m},{cameraState:e}),this.graphToViewport({x:f,y:m},{cameraState:e})],v=1/0,b=-1/0,y=1/0,T=-1/0;p.forEach(function(w){var k=w.x,G=w.y;v=Math.min(v,k),b=Math.max(b,k),y=Math.min(y,G),T=Math.max(T,G)});var x=b-v,_=T-y,R=this.getDimensions(),E=R.width,L=R.height,D=0,F=0;if(x>=E?b<E-o?D=b-(E-o):v>o&&(D=v-o):b>E+o?D=b-(E+o):v<-o&&(D=v+o),_>=L?T<L-o?F=T-(L-o):y>o&&(F=y-o):T>L+o?F=T-(L+o):y<-o&&(F=y+o),D||F){var A=this.viewportToFramedGraph({x:0,y:0},{cameraState:e}),I=this.viewportToFramedGraph({x:D,y:F},{cameraState:e});D=I.x-A.x,F=I.y-A.y,l.x+=D,l.y+=F}return l}},{key:"refreshMatrices",value:function(){var e=this.camera.getState(),r=this.getDimensions(),i=this.getGraphDimensions(),o=this.getStagePadding();this.matrix=Pe(e,r,i,o),this.invMatrix=Pe(e,r,i,o,!0),this.correctionRatio=Ja(this.matrix,e,r),this.graphToViewportRatio=this.getGraphToViewportRatio()}},{key:"processData",value:function(){var e;this.emit("beforeProcess"),(e=this.internals.attachmentManager)===null||e===void 0||e.clear();var r=B({},this.pickingState.idsByKind),i=this.processNodes();(this.pendingProcess==="full"||i)&&this.processEdges(),cd(this.pickingState,this.internals),hd(r,this.pickingState.idsByKind)||this.internals.hoverResolver.invalidate(),this.pendingProcess="none",this.emit("afterProcess")}},{key:"render",value:function(){var e=this;if(this.contextLost)return this;this.emit("beforeRender");var r=function(){return e.internals.hoverResolver.frameRendered(),e.emit("afterRender"),e};if(this.renderFrame&&(cancelAnimationFrame(this.renderFrame),this.renderFrame=null),this.resize(),(this.pendingProcess!=="none"||this.needToRefreshState)&&(this.labelRenderer.labelsDirty=!0),this.pendingProcess!=="none"&&this.processData(),this.needToRefreshState&&this.refreshState(),this.needToRefreshState=!1,this.stateManager.clearDirtyTracking(),this.pendingProcess!=="none"&&this.processData(),this.clear(),this.resetWebGLTexture(),!this.internals.graph.order)return r();var i=this.mouseCaptor,o=this.camera.isAnimating()||i.isMoving||i.draggedEvents||i.currentWheelDirection;if(this.refreshMatrices(),this.frameId++,this.internals.settings.renderEdgeLabels&&!this.internals.edgeLabelProgram){var s=this.createEdgeLabelPrograms(),l=s.labelProgram,u=s.labelBackgroundProgram;this.internals.edgeLabelProgram=l,this.internals.edgeLabelBackgroundProgram=u}var d=this.internals.settings.DEBUG_logRenderStats?this.getDebugPrograms():null;d&&d.forEach(function(j){return j.resetDebugStats()}),this.internals.settings.DEBUG_gpuTimerQueries&&this.beginGpuTimerQuery(),this.internals.nodeFrameTexture.ensureCapacity(this.internals.nodeDataTexture.getCapacity()),this.internals.edgeFrameTexture.ensureCapacity(this.internals.edgeDataTexture.getCapacity());var c=this.getRenderParams(),f=se.edge.writesPickingThisFrame(this.internals)?c:B(B({},c),{},{pickingFrameBuffer:null});this.labelRenderer.resetFrame();var h=this.webGLContext,g=Math.ceil(this.width*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio),m=Math.ceil(this.height*this.internals.pixelRatio/this.internals.settings.pickingDownSizingRatio);if(h.bindFramebuffer(h.FRAMEBUFFER,this.pickingFrameBuffer),h.viewport(0,0,g,m),h.clear(h.COLOR_BUFFER_BIT|h.DEPTH_BUFFER_BIT),h.bindFramebuffer(h.FRAMEBUFFER,null),h.viewport(0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio),h.clear(h.COLOR_BUFFER_BIT|h.DEPTH_BUFFER_BIT),this.internals.nodeDataTexture.upload(),this.internals.edgeDataTexture.upload(),this.nodeProgram.uploadLayerTexture(),this.edgeProgram.uploadAttributeTexture(),this.emit("afterTexturesUpload"),this.internals.nodeDataTexture.bind(Gi),this.internals.edgeDataTexture.bind(zi),this.edgeFramePass.run(c,this.internals.edgeFrameTexture,this.internals.edgeDataTexture.getHighWaterMark(),this.edgeProgram.getAttributeTexture(),this.nodeProgram.getAttributeTexture()),this.internals.edgeFrameTexture.bind(Ii),this.internals.settings.renderLabels){this.labelRenderer.computeDisplayedNodeLabels();var p=this.labelRenderer.buildFramePassPoints(),v=p.data,b=p.count;this.nodeFramePass.run(v,b,this.internals.nodeFrameTexture,c,this.nodeProgram.getAttributeTexture()),this.internals.nodeFrameTexture.bind(Ni)}this.internals.settings.renderEdgeLabels&&this.labelRenderer.computeDisplayedEdgeLabels();var y=M(this.customLayerPrograms.values()),T;try{for(y.s();!(T=y.n()).done;){var x=T.value.program;x.preRender&&x.preRender(c)}}catch(j){y.e(j)}finally{y.f()}h.bindFramebuffer(h.FRAMEBUFFER,null),h.viewport(0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio),h.blendFunc(h.ONE,h.ONE_MINUS_SRC_ALPHA);var _=!this.internals.settings.hideLabelsOnMove||!o,R=M(this.depthLayers),E;try{for(R.s();!(E=R.n()).done;){var L=E.value,D=M(this.customLayerPrograms.values()),F;try{for(D.s();!(F=D.n()).done;){var A=F.value;A.depth===L&&A.program.render(c)}}catch(j){D.e(j)}finally{D.f()}var I=this.depthRanges.edges[L];if(I&&(!this.internals.settings.hideEdgesOnMove||!o)){var w=M(I),k;try{for(w.s();!(k=w.n()).done;){var G=k.value,N=G.offset,P=G.count;P>0&&this.edgeProgram.render(f,N,P)}}catch(j){w.e(j)}finally{w.f()}}this.internals.settings.renderEdgeLabels&&_&&(this.labelRenderer.renderEdgeLabelBackgrounds(se.edgeLabel.writesPickingThisFrame(this.internals)?c:B(B({},c),{},{pickingFrameBuffer:null}),L),this.labelRenderer.renderEdgeLabels(c,L)),this.labelRenderer.cacheAttachments(L),this.labelRenderer.renderBackdrops(B(B({},c),{},{pickingFrameBuffer:null}),L);var C=this.depthRanges.nodes[L];if(C){var z=M(C),H;try{for(z.s();!(H=z.n()).done;){var U=H.value,q=U.offset,X=U.count;X>0&&this.nodeProgram.render(c,q,X)}}catch(j){z.e(j)}finally{z.f()}}_&&(this.labelRenderer.renderAttachments(B(B({},c),{},{pickingFrameBuffer:null}),L),this.labelRenderer.renderLabelBackgrounds(se.nodeLabel.writesPickingThisFrame(this.internals)?c:B(B({},c),{},{pickingFrameBuffer:null}),L),this.internals.settings.renderLabels&&this.labelRenderer.renderWebGLLabels(c,L))}}catch(j){R.e(j)}finally{R.f()}return this.labelRenderer.labelsDirty=!1,this.internals.settings.DEBUG_displayPickingLayer&&(h.bindFramebuffer(h.READ_FRAMEBUFFER,this.pickingFrameBuffer),h.bindFramebuffer(h.DRAW_FRAMEBUFFER,null),h.blitFramebuffer(0,0,g,m,0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio,h.COLOR_BUFFER_BIT,h.NEAREST)),this.internals.settings.DEBUG_gpuTimerQueries&&this.endGpuTimerQuery(),this.pollGpuTimerQueries(),d&&this.logRenderStats(d),r()}},{key:"getDebugPrograms",value:function(){return[this.nodeProgram,this.edgeProgram,this.internals.labelProgram,this.internals.edgeLabelProgram,this.internals.edgeLabelBackgroundProgram,this.internals.backdropProgram,this.internals.labelBackgroundProgram,this.internals.attachmentProgram].filter(function(e){return e!==null})}},{key:"logRenderStats",value:function(e){var r={},i=M(e),o;try{for(i.s();!(o=i.n()).done;){var s=o.value;r[s.constructor.name]=B({},s.debugStats)}}catch(l){i.e(l)}finally{i.f()}console.log("[sigma] DEBUG_logRenderStats: frame #".concat(this.frameId)),console.table(r)}},{key:"getGpuTimerExtension",value:function(){return this.gpuTimerExt===void 0&&(this.gpuTimerExt=this.webGLContext.getExtension("EXT_disjoint_timer_query_webgl2"),this.gpuTimerExt||console.warn("Sigma: DEBUG_gpuTimerQueries is enabled, but this browser/driver doesn't support EXT_disjoint_timer_query_webgl2.")),this.gpuTimerExt}},{key:"beginGpuTimerQuery",value:function(){var e=this.getGpuTimerExtension();if(e){var r=this.webGLContext,i=r.createQuery();i&&(r.beginQuery(e.TIME_ELAPSED_EXT,i),this.activeGpuTimerQuery=i)}}},{key:"endGpuTimerQuery",value:function(){!this.gpuTimerExt||!this.activeGpuTimerQuery||(this.webGLContext.endQuery(this.gpuTimerExt.TIME_ELAPSED_EXT),this.pendingGpuTimerQueries.push({query:this.activeGpuTimerQuery,frameId:this.frameId}),this.activeGpuTimerQuery=null)}},{key:"pollGpuTimerQueries",value:function(){if(this.pendingGpuTimerQueries.length!==0){var e=this.webGLContext,r=this.gpuTimerExt;if(!r){this.pendingGpuTimerQueries.forEach(function(c){var f=c.query;return e.deleteQuery(f)}),this.pendingGpuTimerQueries=[];return}var i=e.getParameter(r.GPU_DISJOINT_EXT),o=[],s=M(this.pendingGpuTimerQueries),l;try{for(s.s();!(l=s.n()).done;){var u=l.value;if(!e.getQueryParameter(u.query,e.QUERY_RESULT_AVAILABLE)){o.push(u);continue}if(!i){var d=e.getQueryParameter(u.query,e.QUERY_RESULT);console.log("[sigma] DEBUG_gpuTimerQueries: frame #".concat(u.frameId," GPU time = ").concat((d/1e6).toFixed(2),"ms"))}e.deleteQuery(u.query)}}catch(c){s.e(c)}finally{s.f()}this.pendingGpuTimerQueries=o}}},{key:"postEvaluateNode",value:function(e,r,i){var o=e;o.x===void 0&&(o.x=r.x),o.y===void 0&&(o.y=r.y),e.highlighted=i.isHighlighted;for(var s=0,l=this.nodeVariableEntries.length;s<l;s++){var u,d,c=Q(this.nodeVariableEntries[s],2),f=c[0],h=c[1];o[f]=(u=(d=o[f])!==null&&d!==void 0?d:r[f])!==null&&u!==void 0?u:h.default}}},{key:"addNode",value:function(e){var r=this.internals.graph.getNodeAttributes(e),i=this.stateManager.getNodeState(e),o=this.internals.nodeDataCache[e]||{};if(Qn(this.stylesDeclaration.nodes,r,i,this.stateManager.graphState,this.internals.graph,o),this.postEvaluateNode(o,r,i),this.nodeReducer){var s=this.nodeReducer(e,o,r,i,this.stateManager.graphState,this.internals.graph);o=B(B({},o),s)}if(typeof o.x!="number"||typeof o.y!="number")throw new Error('Sigma: could not find a valid position (x, y) for node "'.concat(e,'". ')+"Provide coordinates via node attributes, styles, or a nodeReducer.");this.internals.nodeShapeMap?(!o.shape||!(o.shape in this.internals.nodeShapeMap))&&(o.shape=Object.keys(this.internals.nodeShapeMap)[0]):this.nodeShapeSlug&&(o.shape=this.nodeShapeSlug),this.internals.nodeDataCache[e]=o,this.nodeGraphCoords[e]={x:o.x,y:o.y},We(this.internals.nodesWithForcedLabels,e,Fe(o)),We(this.internals.nodesWithBackdrop,e,aa(o)),this.itemBuckets.nodes.set(e,o.depth)}},{key:"updateNode",value:function(e){this.addNode(e);var r=this.internals.nodeDataCache[e];this.normalizationFunction.applyTo(r)}},{key:"removeNode",value:function(e){wi(this.pickingState,"node",e),this.itemBuckets.nodes.remove(e),delete this.internals.nodeDataCache[e],delete this.nodeGraphCoords[e],delete this.nodeProgramIndex[e],this.internals.nodeDataTexture.free(e),this.internals.dragManager.removeNode(e),this.stateManager.removeNode(e),this.internals.nodesWithForcedLabels.delete(e),this.internals.nodesWithBackdrop.delete(e)}},{key:"postEvaluateEdge",value:function(e,r){for(var i=e,o=0,s=this.edgeVariableEntries.length;o<s;o++){var l,u,d=Q(this.edgeVariableEntries[o],2),c=d[0],f=d[1];i[c]=(l=(u=i[c])!==null&&u!==void 0?u:r[c])!==null&&l!==void 0?l:f.default}}},{key:"applyEdgeSpread",value:function(e,r,i){var o;if(!(i.parallelCount<=1)){var s=this.internals.graph.source(e),l=this.internals.graph.target(e),u=s===l,d=u?r.selfLoopPath||r.path:r.parallelPath||r.path,c=d?this.edgePathsByName.get(d):void 0;if(c!=null&&c.spread){var f=(o=r.parallelSpread)!==null&&o!==void 0?o:.25,h=c.spread.compute(i.parallelIndex,i.parallelCount,f);!u&&this.internals.graph.isDirected(e)&&s>l&&(h=-h),r[c.spread.variable]=h}}}},{key:"addEdge",value:function(e){var r=this.internals.graph.getEdgeAttributes(e),i=this.stateManager.getEdgeState(e),o={};if(Jn(this.stylesDeclaration.edges,r,i,this.stateManager.graphState,this.internals.graph,o),this.postEvaluateEdge(o,r),this.edgeReducer){var s=this.edgeReducer(e,o,r,i,this.stateManager.graphState,this.internals.graph);o=B(B({},o),s)}this.applyEdgeSpread(e,o,i),this.internals.edgeDataCache[e]=o,We(this.internals.edgesWithForcedLabels,e,Fe(o)),this.itemBuckets.edges.set(e,o.depth)}},{key:"updateEdge",value:function(e){this.addEdge(e)}},{key:"removeEdge",value:function(e){this.itemBuckets.edges.remove(e),delete this.internals.edgeDataCache[e],delete this.edgeProgramIndex[e],delete this.edgeTextureIndexCache[e],this.internals.edgeDataTexture.free(e),wi(this.pickingState,"edge",e),this.stateManager.removeEdge(e),this.internals.edgesWithForcedLabels.delete(e)}},{key:"clearNodeIndices",value:function(){var e;this.labelRenderer.resetLabelGrid(),this.autoRescaleFrozen||(this.nodeExtent={x:[0,1],y:[0,1]}),this.internals.nodeDataCache={},this.nodeGraphCoords={},this.nodeProgramIndex={},(e=this.internals.nodeDataTexture)===null||e===void 0||e.clear(),this.internals.nodesWithForcedLabels.clear(),this.internals.nodesWithBackdrop.clear(),this.prevNodeVisibilities={},this.itemBuckets.nodes.clearAll(),this.depthRanges.nodes={},this.nodeBaseDepth={}}},{key:"clearEdgeIndices",value:function(){var e;this.internals.edgeDataCache={},this.edgeProgramIndex={},this.edgeTextureIndexCache={},(e=this.internals.edgeDataTexture)===null||e===void 0||e.clear(),this.internals.edgesWithForcedLabels.clear(),this.itemBuckets.edges.clearAll(),this.depthRanges.edges={},this.edgeBaseDepth={},this.edgeGroups.clear()}},{key:"clearIndices",value:function(){this.clearEdgeIndices(),this.clearNodeIndices()}},{key:"clearNodeState",value:function(){this.labelRenderer.resetFrame(),this.internals.nodesWithBackdrop.clear(),this.internals.dragManager.clear(),this.autoRescaleFrozen=!1,this.stateManager.clearNodes(),wn(this.pickingState,"node")}},{key:"clearEdgeState",value:function(){this.labelRenderer.clearEdgeLabels(),this.stateManager.clearEdges(),wn(this.pickingState,"edge")}},{key:"clearState",value:function(){this.clearEdgeState(),this.clearNodeState(),this.stateManager.resetGraphState()}},{key:"addNodeToProgram",value:function(e,r){var i,o=this.internals.nodeDataCache[e];this.internals.nodeDataTexture.allocate(e),(i=this.internals.nodeDataTexture).updateNode.apply(i,[e,o.x,o.y,o.size,this.getNodeShapeId(o)].concat($(dn(o)),[o.color]));var s=this.internals.nodeDataTexture.getIndex(e);this.nodeProgram.process(Xe(this.pickingState,"node",e),r,o,s),this.nodeProgramIndex[e]=r}},{key:"addEdgeToProgram",value:function(e,r){var i,o,s=this.internals.edgeDataCache[e],l=this.internals.graph.source(e),u=this.internals.graph.target(e),d=this.internals.edgeDataTexture.allocate(e);this.edgeTextureIndexCache[e]=d;var c=l===u,f=!c&&((i=(o=this.stateManager.getEdgeState(e))===null||o===void 0?void 0:o.parallelCount)!==null&&i!==void 0?i:1)>1,h=this.edgeProgram.resolveEdgeIds(s,c,f),g=h.pathId,m=h.headId,p=h.tailId,v=h.headLengthRatio,b=h.tailLengthRatio;this.internals.edgeDataTexture.updateEdge(e,this.internals.nodeDataTexture.getIndex(l),this.internals.nodeDataTexture.getIndex(u),s.size,v,b,g,m,p),this.edgeProgram.process(Xe(this.pickingState,"edge",e),r,this.internals.nodeDataCache[l],this.internals.nodeDataCache[u],s,d),this.edgeProgramIndex[e]=r}},{key:"getRenderParams",value:function(){return{frameId:this.frameId,matrix:this.matrix,invMatrix:this.invMatrix,width:this.width,height:this.height,pixelRatio:this.internals.pixelRatio,zoomRatio:this.camera.ratio,cameraAngle:this.camera.angle,sizeRatio:1/this.scaleSize(),correctionRatio:this.correctionRatio,downSizingRatio:this.internals.settings.pickingDownSizingRatio,minEdgeThickness:this.internals.settings.minEdgeThickness,antiAliasingFeather:this.internals.settings.antiAliasingFeather,nodePickingPadding:this.internals.settings.nodePickingPadding,edgePickingPadding:this.internals.settings.edgePickingPadding,labelPickingPadding:this.internals.settings.labelPickingPadding,nodeDataTextureUnit:Gi,nodeDataTextureWidth:this.internals.nodeDataTexture.getTextureWidth(),nodeFrameTextureUnit:Ni,nodeFrameTextureWidth:this.internals.nodeFrameTexture.getTextureWidth(),edgeDataTextureUnit:zi,edgeDataTextureWidth:this.internals.edgeDataTexture.getTextureWidth(),edgeFrameTextureUnit:Ii,edgeFrameTextureWidth:this.internals.edgeFrameTexture.getTextureWidth(),pickingFrameBuffer:this.pickingFrameBuffer,labelPixelSnapping:this.internals.settings.labelPixelSnapping?1:0}}},{key:"getStagePadding",value:function(){var e=this.internals.settings,r=e.stagePadding,i=e.autoRescale;return i&&r||0}},{key:"getLayerElement",value:function(e){if(e==="mouse")return this.mouseLayer;var r=this.extraElements[e];if(!r)throw new Error('Sigma: layer "'.concat(e,'" does not exist'));return r}},{key:"initWebGLContext",value:function(){var e=this,r=this.createWebGLContext("stage");this.stageCanvas=this.extraElements.stage,this.webGLContext=r,this.stageCanvas.addEventListener("webglcontextlost",function(i){e.webGLContext&&(i.preventDefault(),e.contextLost=!0,e.renderFrame&&(cancelAnimationFrame(e.renderFrame),e.renderFrame=null),e.gpuTimerExt=void 0,e.activeGpuTimerQuery=null,e.pendingGpuTimerQueries=[],e.emit("webglContextLost"))}),this.stageCanvas.addEventListener("webglcontextrestored",function(){requestAnimationFrame(function(){e.webGLContext&&!e.webGLContext.isContextLost()&&e.restoreWebGLContext()})}),this.initPickingFramebuffer()}},{key:"initPickingFramebuffer",value:function(){var e=this.webGLContext,r=e.createFramebuffer();if(!r)throw new Error("Sigma: cannot create picking frame buffer");e.bindFramebuffer(e.FRAMEBUFFER,r);var i=e.createTexture();if(!i)throw new Error("Sigma: cannot create picking texture");e.bindTexture(e.TEXTURE_2D,i),e.texImage2D(e.TEXTURE_2D,0,e.RGBA,1,1,0,e.RGBA,e.UNSIGNED_BYTE,null),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MIN_FILTER,e.NEAREST),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_MAG_FILTER,e.NEAREST),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_S,e.CLAMP_TO_EDGE),e.texParameteri(e.TEXTURE_2D,e.TEXTURE_WRAP_T,e.CLAMP_TO_EDGE),e.framebufferTexture2D(e.FRAMEBUFFER,e.COLOR_ATTACHMENT0,e.TEXTURE_2D,i,0);var o=e.createRenderbuffer();if(!o)throw new Error("Sigma: cannot create picking depth buffer");if(e.bindRenderbuffer(e.RENDERBUFFER,o),e.renderbufferStorage(e.RENDERBUFFER,e.DEPTH_COMPONENT16,1,1),e.framebufferRenderbuffer(e.FRAMEBUFFER,e.DEPTH_ATTACHMENT,e.RENDERBUFFER,o),e.checkFramebufferStatus(e.FRAMEBUFFER)!==e.FRAMEBUFFER_COMPLETE)throw new Error("Sigma: picking framebuffer is not complete");e.bindFramebuffer(e.FRAMEBUFFER,null),this.pickingFrameBuffer=r,this.pickingTexture=i,this.pickingDepthBuffer=o}},{key:"initPrograms",value:function(e,r){var i=this,o=this.webGLContext,s=ci(o,this.pickingFrameBuffer,i,e?.nodes,r.antialiasNodes),l=s.nodeProgram,u=s.labelProgram,d=s.backdropProgram,c=s.labelBackgroundProgram,f=s.attachmentProgram,h=s.framePass,g=s.shapeSlug,m=s.shapeNameToIndex,p=s.shapeGlobalIds,v=s.variables;this.nodeProgram=l,this.nodeFramePass=h,this.nodeVariableEntries=Object.entries(v),g&&(this.nodeShapeSlug=g);var b=hi(o,this.pickingFrameBuffer,i,e?.edges,r.antialiasEdges,e?.nodes),y=b.edgeProgram,T=b.createLabelPrograms,x=b.framePass,_=b.variables,R=b.paths;return this.createEdgeLabelPrograms=T,this.edgeProgram=y,this.edgeFramePass=x,this.edgeVariableEntries=Object.entries(_),this.edgePathsByName=new Map(R.map(function(E){return[E.name,E]})),{labelProgram:u,edgeLabelProgram:null,edgeLabelBackgroundProgram:null,backdropProgram:d,labelBackgroundProgram:c,attachmentProgram:f,nodeShapeMap:m??null,nodeGlobalShapeIds:p??null}}},{key:"restoreWebGLContext",value:function(){var e,r,i,o,s,l=this.internals;this.initPickingFramebuffer(),(e=l.nodeDataTexture)===null||e===void 0||e.restore(),(r=l.nodeFrameTexture)===null||r===void 0||r.restore(),(i=l.edgeDataTexture)===null||i===void 0||i.restore(),(o=l.edgeFrameTexture)===null||o===void 0||o.restore(),(s=l.attachmentManager)===null||s===void 0||s.restore(),l.hoverResolver.reset(),Object.assign(l,this.initPrograms(l.primitives,l.settings));var u=M(this.customLayerPrograms.values()),d;try{for(u.s();!(d=u.n()).done;){var c=d.value;c.program.kill(),c.program=c.factory(this.webGLContext)}}catch(f){u.e(f)}finally{u.f()}this.contextLost=!1,this.emit("webglContextRestored"),this.refresh()}},{key:"createLayer",value:function(e,r){var i=arguments.length>2&&arguments[2]!==void 0?arguments[2]:{};if(this.extraElements[e])throw new Error('Sigma: a layer named "'.concat(e,'" already exists'));var o=st(r,{position:"absolute"},{class:"sigma-".concat(e)});return i.style&&Object.assign(o.style,i.style),this.extraElements[e]=o,"beforeLayer"in i&&i.beforeLayer?this.getLayerElement(i.beforeLayer).before(o):"afterLayer"in i&&i.afterLayer?this.getLayerElement(i.afterLayer).after(o):this.container.appendChild(o),o}},{key:"createCanvas",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};return this.createLayer(e,"canvas",r)}},{key:"createWebGLContext",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=this.createCanvas(e,r);r.hidden&&i.remove();var o=i.getContext("webgl2",B({preserveDrawingBuffer:!1,antialias:!1,depth:!0},r));if(!o)throw new Error("Sigma: WebGL 2 is not supported by your browser. Please use a modern browser (Chrome 56+, Firefox 51+, Safari 15+, Edge 79+).");return o.blendFunc(o.ONE,o.ONE_MINUS_SRC_ALPHA),o}},{key:"killLayer",value:function(e){if(e==="stage"||e==="mouse")throw new Error('Sigma: cannot kill built-in layer "'.concat(e,'"'));var r=this.extraElements[e];if(!r)throw new Error("Sigma: cannot kill layer ".concat(e,", which does not exist"));return r.remove(),delete this.extraElements[e],this}},{key:"getWebGLContext",value:function(){if(!this.webGLContext)throw new Error("Sigma: WebGL context is not available");return this.webGLContext}},{key:"getNodeDataTexture",value:function(){if(!this.internals.nodeDataTexture)throw new Error("Sigma: node data texture is not available");return this.internals.nodeDataTexture}},{key:"getNormalizationFunction",value:function(){return this.normalizationFunction}},{key:"addCustomLayerProgram",value:function(e,r,i){var o;if(!this.depthLayers.includes(r))throw new Error('Sigma: cannot add custom layer program at depth "'.concat(r,'", ')+"it must be declared in primitives.depthLayers. Current layers: ".concat(this.depthLayers.join(", ")));(o=this.customLayerPrograms.get(e))===null||o===void 0||o.program.kill();var s=i(this.webGLContext);return this.customLayerPrograms.set(e,{depth:r,factory:i,program:s}),s.cacheData&&s.cacheData(),this.scheduleRender(),this}},{key:"removeCustomLayerProgram",value:function(e){var r=this.customLayerPrograms.get(e);return r&&(r.program.kill(),this.customLayerPrograms.delete(e),this.scheduleRender()),this}},{key:"getCamera",value:function(){return this.camera}},{key:"setCamera",value:function(e){return this.camera.cancelAnimation(),this.unbindCameraHandlers(),this.camera=e,this.bindCameraHandlers(),this.scheduleRender(),this}},{key:"getContainer",value:function(){return this.container}},{key:"getGraph",value:function(){return this.internals.graph}},{key:"setGraph",value:function(e){return e===this.internals.graph?this:(this.stateManager.pruneNodes(function(r){return e.hasNode(r)}),this.stateManager.pruneEdges(function(r){return e.hasEdge(r)}),this.unbindGraphHandlers(),this.checkEdgesEventsFrame!==null&&(cancelAnimationFrame(this.checkEdgesEventsFrame),this.checkEdgesEventsFrame=null),this.internals.graph=e,this.autoRescaleFrozen=!1,this.bindGraphHandlers(),this.refresh(),this)}},{key:"getMouseCaptor",value:function(){return this.mouseCaptor}},{key:"getTouchCaptor",value:function(){return this.touchCaptor}},{key:"getDimensions",value:function(){return{width:this.width,height:this.height}}},{key:"getGraphDimensions",value:function(){var e=this.customBBox||this.nodeExtent;return{width:e.x[1]-e.x[0]||1,height:e.y[1]-e.y[0]||1}}},{key:"getNodeDisplayData",value:function(e){var r=this.internals.nodeDataCache[e];return r?Object.assign({},r):void 0}},{key:"getEdgeDisplayData",value:function(e){var r=this.internals.edgeDataCache[e];return r?Object.assign({},r):void 0}},{key:"getNodeState",value:function(e){return this.stateManager.getNodeState(e)}},{key:"getEdgeState",value:function(e){return this.stateManager.getEdgeState(e)}},{key:"getGraphState",value:function(){return this.stateManager.getGraphState()}},{key:"setNodeState",value:function(e,r){return this.stateManager.setNodeState(e,r),this}},{key:"setEdgeState",value:function(e,r){return this.stateManager.setEdgeState(e,r),this}},{key:"setGraphState",value:function(e){return this.stateManager.setGraphState(e),this}},{key:"_setPanning",value:function(e){this.stateManager.setGraphState({isPanning:e})}},{key:"_setZooming",value:function(e){this.stateManager.setGraphState({isZooming:e})}},{key:"_hasNodeDrag",value:function(){var e=this.internals.dragManager;return!!(e.pendingNode||e.session)}},{key:"_showGestureHint",value:function(e){var r=this.internals.settings;r.gestureTarget==="shared"&&(this.gestureHint=this.gestureHint||new wd(this.container),this.gestureHint.show(e,r))}},{key:"setNodesState",value:function(e,r){return this.stateManager.setNodesState(e,r),this}},{key:"setEdgesState",value:function(e,r){return this.stateManager.setEdgesState(e,r),this}},{key:"updateContainerCursor",value:function(){var e=this.stateManager.hovered,r=this.resolvedStageStyle.cursor||"";this.container.style.cursor=e&&fd(this.internals,e)||r}},{key:"refreshStageStyle",value:function(){this.resolvedStageStyle=ea(this.stylesDeclaration.stage,this.stateManager.graphState),this.resolvedStageStyle.background!==void 0&&(this.container.style.backgroundColor=this.resolvedStageStyle.background),this.updateContainerCursor()}},{key:"getNodeDisplayedLabels",value:function(){return new Set(this.labelRenderer.displayedNodeLabels)}},{key:"getEdgeDisplayedLabels",value:function(){return new Set(this.labelRenderer.displayedEdgeLabels)}},{key:"getSettings",value:function(){return B({},this.internals.settings)}},{key:"getSetting",value:function(e){return this.internals.settings[e]}},{key:"getStyles",value:function(){return B({},this.stylesDeclaration)}},{key:"getPrimitives",value:function(){return B({},this.internals.primitives)}},{key:"setSetting",value:function(e,r){return this.internals.settings[e]=r,fn(this.internals.settings),this.handleSettingsUpdate(),this.scheduleRefresh(),this}},{key:"updateSetting",value:function(e,r){return this.setSetting(e,r(this.internals.settings[e])),this}},{key:"setSettings",value:function(e){return this.internals.settings=B(B({},this.internals.settings),e),fn(this.internals.settings),this.handleSettingsUpdate(),this.scheduleRefresh(),this}},{key:"resize",value:function(e){var r=this.width,i=this.height;if(this.width=this.container.offsetWidth,this.height=this.container.offsetHeight,this.internals.pixelRatio=Dt(),this.width===0)if(this.internals.settings.allowInvalidContainer)this.width=1;else throw new Error("Sigma: Container has no width. You can set the allowInvalidContainer setting to true to stop seeing this error.");if(this.height===0)if(this.internals.settings.allowInvalidContainer)this.height=1;else throw new Error("Sigma: Container has no height. You can set the allowInvalidContainer setting to true to stop seeing this error.");if(!e&&r===this.width&&i===this.height)return this;this.labelRenderer.labelsDirty=!0;for(var o=0,s=[this.mouseLayer].concat($(Object.values(this.extraElements)));o<s.length;o++){var l=s[o];l.style.width=this.width+"px",l.style.height=this.height+"px"}return this.webGLContext&&(this.stageCanvas.setAttribute("width",this.width*this.internals.pixelRatio+"px"),this.stageCanvas.setAttribute("height",this.height*this.internals.pixelRatio+"px"),this.webGLContext.viewport(0,0,this.width*this.internals.pixelRatio,this.height*this.internals.pixelRatio)),this.emit("resize"),this}},{key:"clear",value:function(){return this.emit("beforeClear"),this.webGLContext.bindFramebuffer(WebGLRenderingContext.FRAMEBUFFER,null),this.webGLContext.clear(WebGLRenderingContext.COLOR_BUFFER_BIT),this.emit("afterClear"),this}},{key:"scheduleStateRefresh",value:function(){this.needToRefreshState=!0,this.scheduleRender()}},{key:"refreshState",value:function(){var e=this,r;this.stateManager.flushGraphStateFlags();var i=this.stateManager.graphStateChanged&&this.internals.nodeStyleAnalysis.dependency==="graph-state",o=this.stateManager.graphStateChanged&&this.edgeStyleAnalysis.dependency==="graph-state",s=!1;if(i)this.internals.graph.forEachNode(function(g){e.refreshNodeState(g)&&(s=!0)});else if(this.internals.nodeStyleAnalysis.dependency!=="static"){var l=M(this.stateManager.dirtyNodes),u;try{for(l.s();!(u=l.n()).done;){var d=u.value;this.refreshNodeState(d)&&(s=!0)}}catch(g){l.e(g)}finally{l.f()}}if(o)this.internals.graph.forEachEdge(function(g){e.refreshEdgeState(g)&&(s=!0)});else if(this.edgeStyleAnalysis.dependency!=="static"){var c=M(this.stateManager.dirtyEdges),f;try{for(c.s();!(f=c.n()).done;){var h=f.value;this.refreshEdgeState(h)&&(s=!0)}}catch(g){c.e(g)}finally{c.f()}}this.stateManager.graphStateChanged&&(r=this.stylesDeclaration)!==null&&r!==void 0&&r.stage&&this.refreshStageStyle(),this.stateManager.clearDirtyTracking(),s&&(this.pendingProcess="full")}},{key:"refreshNodeState",value:function(e){var r=this.internals.nodeDataCache[e];if(!r||this.nodeReducer){var i,o,s,l,u=(i=this.internals.nodeDataCache[e])===null||i===void 0?void 0:i.depth,d=(o=this.internals.nodeDataCache[e])===null||o===void 0?void 0:o.zIndex,c=(s=this.internals.nodeDataCache[e])===null||s===void 0?void 0:s.labelAttachment;this.updateNode(e);var f=this.internals.nodeDataCache[e];this.internals.attachmentManager&&f.labelAttachment!==c&&this.internals.attachmentManager.invalidateNode(e);var h;this.internals.nodeShapeMap&&this.internals.nodeGlobalShapeIds&&f.shape&&f.shape in this.internals.nodeShapeMap?h=this.internals.nodeGlobalShapeIds[this.internals.nodeShapeMap[f.shape]]:h=kt(f.shape||"circle"),(l=this.internals.nodeDataTexture).updateNode.apply(l,[e,f.x,f.y,f.size,h].concat($(dn(f)),[f.color])),u&&f.depth!==u&&this.updateNodeDepthRanges(e,u,f.depth);var g=this.nodeProgramIndex[e];return g!==void 0&&(this.addNodeToProgram(e,g),this.nodeProgram.invalidateBuffers()),d!==void 0&&f.zIndex!==d}var m=this.internals.graph.getNodeAttributes(e),p=this.stateManager.getNodeState(e),v=r.size,b=r.shape,y=r.depth,T=r.zIndex,x=r.labelAttachment,_=r.rotationAlignment,R=r.labelRotationAlignment,E=r.color;Qn(this.stylesDeclaration.nodes,m,p,this.stateManager.graphState,this.internals.graph,r),this.postEvaluateNode(r,m,p);var L=this.nodeGraphCoords[e],D=r.x!==L.x||r.y!==L.y;if(D&&(L.x=r.x,L.y=r.y),this.normalizationFunction.applyTo(r),this.internals.nodeShapeMap?(!r.shape||!(r.shape in this.internals.nodeShapeMap))&&(r.shape=Object.keys(this.internals.nodeShapeMap)[0]):this.nodeShapeSlug&&(r.shape=this.nodeShapeSlug),this.internals.attachmentManager&&r.labelAttachment!==x&&this.internals.attachmentManager.invalidateNode(e),We(this.internals.nodesWithForcedLabels,e,Fe(r)),We(this.internals.nodesWithBackdrop,e,aa(r)),D||r.size!==v||r.shape!==b||r.rotationAlignment!==_||r.labelRotationAlignment!==R||r.color!==E){var F,A;this.internals.nodeShapeMap&&this.internals.nodeGlobalShapeIds&&r.shape&&r.shape in this.internals.nodeShapeMap?A=this.internals.nodeGlobalShapeIds[this.internals.nodeShapeMap[r.shape]]:A=kt(r.shape||"circle"),(F=this.internals.nodeDataTexture).updateNode.apply(F,[e,r.x,r.y,r.size,A].concat($(dn(r)),[r.color]))}this.itemBuckets.nodes.set(e,r.depth),r.depth!==y&&this.updateNodeDepthRanges(e,y,r.depth);var I=this.nodeProgramIndex[e];return I!==void 0&&(this.addNodeToProgram(e,I),this.nodeProgram.invalidateBuffers()),r.zIndex!==T}},{key:"refreshEdgeState",value:function(e){var r=this.internals.edgeDataCache[e];if(!r||this.edgeReducer){var i=r?.depth,o=r?.zIndex;this.updateEdge(e);var s=this.internals.edgeDataCache[e];i&&s.depth!==i&&this.updateEdgeDepthRanges(e,i,s.depth);var l=this.edgeProgramIndex[e];return l!==void 0&&(this.addEdgeToProgram(e,l),this.edgeProgram.invalidateBuffers()),o!==void 0&&s.zIndex!==o}var u=this.internals.graph.getEdgeAttributes(e),d=this.stateManager.getEdgeState(e),c=r.depth,f=r.zIndex,h=r.size,g=r.path,m=r.selfLoopPath,p=r.parallelPath,v=r.head,b=r.tail;Jn(this.stylesDeclaration.edges,u,d,this.stateManager.graphState,this.internals.graph,r),this.postEvaluateEdge(r,u),this.applyEdgeSpread(e,r,d),We(this.internals.edgesWithForcedLabels,e,Fe(r)),this.itemBuckets.edges.set(e,r.depth),r.depth!==c&&this.updateEdgeDepthRanges(e,c,r.depth);var y=this.edgeProgramIndex[e];if(y!==void 0){var T=r.size!==h||r.path!==g||r.selfLoopPath!==m||r.parallelPath!==p||r.head!==v||r.tail!==b;if(T)this.addEdgeToProgram(e,y),this.edgeProgram.invalidateBuffers();else{var x=this.internals.graph.source(e),_=this.internals.graph.target(e),R=this.internals.nodeDataCache[x],E=this.internals.nodeDataCache[_],L=this.edgeTextureIndexCache[e];this.edgeProgram.process(Xe(this.pickingState,"edge",e),y,R,E,r,L),this.edgeProgram.invalidateBuffers()}}return r.zIndex!==f}},{key:"refresh",value:function(e){var r=this,i=e?.skipIndexation!==void 0?e?.skipIndexation:!1,o=e?.schedule!==void 0?e.schedule:!1,s=!e||!e.partialGraph;if(s)this.clearEdgeIndices(),this.clearNodeIndices(),this.internals.graph.forEachNode(function(R){return r.addNode(R)}),this.edgeGroups.rebuild(),this.internals.graph.forEachEdge(function(R){return r.addEdge(R)}),this.pendingProcess="full";else{for(var l,u,d=((l=e.partialGraph)===null||l===void 0?void 0:l.nodes)||[],c=0,f=d?.length||0;c<f;c++){var h,g,m=""+d[c],p=(h=this.internals.nodeDataCache[m])===null||h===void 0?void 0:h.labelAttachment;if(this.updateNode(m),this.internals.attachmentManager&&((g=this.internals.nodeDataCache[m])!==null&&g!==void 0&&g.labelAttachment||p)&&this.internals.attachmentManager.invalidateNode(m),i){var v=this.nodeProgramIndex[m];if(v===void 0)throw new Error('Sigma: node "'.concat(m,`" can't be repaint`));this.addNodeToProgram(m,v)}}i&&d.length>0&&(this.nodeProgram.invalidateBuffers(),this.labelRenderer.labelsDirty=!0);for(var b=(e==null||(u=e.partialGraph)===null||u===void 0?void 0:u.edges)||[],y=0,T=b.length;y<T;y++){var x=""+b[y];if(this.updateEdge(x),i){var _=this.edgeProgramIndex[x];if(_===void 0)throw new Error('Sigma: edge "'.concat(x,`" can't be repaint`));this.addEdgeToProgram(x,_)}}i&&b.length>0&&(this.edgeProgram.invalidateBuffers(),this.labelRenderer.labelsDirty=!0),!i&&this.pendingProcess!=="full"&&(this.pendingProcess=b.length>0?"full":"nodes")}return o?this.scheduleRender():this.render(),this}},{key:"scheduleRender",value:function(){var e=this;return this.renderFrame||(this.renderFrame=requestAnimationFrame(function(){e.render()})),this}},{key:"scheduleRefresh",value:function(e){return this.refresh(B(B({},e),{},{schedule:!0}))}},{key:"getViewportZoomedState",value:function(e,r){var i=this.camera.getState(),o=i.ratio,s=i.angle,l=i.x,u=i.y,d=this.internals.settings,c=d.minCameraRatio,f=d.maxCameraRatio;typeof f=="number"&&(r=Math.min(r,f)),typeof c=="number"&&(r=Math.max(r,c));var h=r/o,g={x:this.width/2,y:this.height/2},m=this.viewportToFramedGraph(e),p=this.viewportToFramedGraph(g);return{angle:s,x:(m.x-p.x)*(1-h)+l,y:(m.y-p.y)*(1-h)+u,ratio:r}}},{key:"viewRectangle",value:function(){var e=this.viewportToFramedGraph({x:0,y:0}),r=this.viewportToFramedGraph({x:this.width,y:0}),i=this.viewportToFramedGraph({x:0,y:this.height});return{x1:e.x,y1:e.y,x2:r.x,y2:r.y,height:r.y-i.y}}},{key:"framedGraphToViewport",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=!!r.cameraState||!!r.viewportDimensions||!!r.graphDimensions||!!r.padding,o=r.matrix||(i?Pe(r.cameraState||this.camera.getState(),r.viewportDimensions||this.getDimensions(),r.graphDimensions||this.getGraphDimensions(),r.padding||this.getStagePadding()):this.matrix),s=nt(o,e);return{x:(1+s.x)*this.width/2,y:(1-s.y)*this.height/2}}},{key:"viewportToFramedGraph",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{},i=!!r.cameraState||!!r.viewportDimensions||!!r.graphDimensions||!!r.padding,o=r.matrix||(i?Pe(r.cameraState||this.camera.getState(),r.viewportDimensions||this.getDimensions(),r.graphDimensions||this.getGraphDimensions(),r.padding||this.getStagePadding(),!0):this.invMatrix),s=nt(o,{x:e.x/this.width*2-1,y:1-e.y/this.height*2});return isNaN(s.x)&&(s.x=0),isNaN(s.y)&&(s.y=0),s}},{key:"viewportToGraph",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};return this.normalizationFunction.inverse(this.viewportToFramedGraph(e,r))}},{key:"graphToViewport",value:function(e){var r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:{};return this.framedGraphToViewport(this.normalizationFunction(e),r)}},{key:"graphToFramedGraph",value:function(e){return this.normalizationFunction(e)}},{key:"framedGraphToGraph",value:function(e){return this.normalizationFunction.inverse(e)}},{key:"getGraphToViewportRatio",value:function(){var e={x:0,y:0},r={x:1,y:1},i=Math.sqrt(Math.pow(e.x-r.x,2)+Math.pow(e.y-r.y,2)),o=this.graphToViewport(e),s=this.graphToViewport(r),l=Math.sqrt(Math.pow(o.x-s.x,2)+Math.pow(o.y-s.y,2));return l/i}},{key:"computeNodeExtent",value:function(){var e=this.nodeGraphCoords,r=Object.keys(e);if(!r.length)return{x:[0,1],y:[0,1]};for(var i=1/0,o=-1/0,s=1/0,l=-1/0,u=0,d=r.length;u<d;u++){var c=e[r[u]],f=c.x,h=c.y;f<i&&(i=f),f>o&&(o=f),h<s&&(s=h),h>l&&(l=h)}return{x:[i,o],y:[s,l]}}},{key:"getBBox",value:function(){return this.nodeExtent}},{key:"getCustomBBox",value:function(){return this.customBBox}},{key:"setCustomBBox",value:function(e){return this.customBBox=e,this.scheduleRender(),this}},{key:"kill",value:function(){var e,r,i,o,s;this.emit("kill"),this.removeAllListeners(),this.camera.cancelAnimation(),this.unbindCameraHandlers(),window.removeEventListener("resize",this.activeListeners.handleResize),this.mouseCaptor.kill(),this.touchCaptor.kill(),this.internals.hoverResolver.kill(),this.unbindGraphHandlers(),this.clearIndices(),this.clearState(),this.internals.nodeDataCache={},this.internals.edgeDataCache={},this.renderFrame&&(cancelAnimationFrame(this.renderFrame),this.renderFrame=null);for(var l=this.container;l.firstChild;)l.removeChild(l.firstChild);this.nodeProgram.kill(),this.nodeFramePass.kill(),this.edgeProgram.kill(),this.edgeFramePass.kill(),this.internals.labelProgram.kill(),(e=this.internals.edgeLabelProgram)===null||e===void 0||e.kill(),(r=this.internals.edgeLabelBackgroundProgram)===null||r===void 0||r.kill(),this.internals.backdropProgram.kill(),this.internals.labelBackgroundProgram.kill(),(i=this.internals.attachmentProgram)===null||i===void 0||i.kill(),(o=this.internals.attachmentManager)===null||o===void 0||o.kill(),this.internals.attachmentProgram=null,this.internals.attachmentManager=null;var u=M(this.customLayerPrograms.values()),d;try{for(u.s();!(d=u.n()).done;){var c=d.value.program;c.kill()}}catch(g){u.e(g)}finally{u.f()}if(this.customLayerPrograms.clear(),this.sdfAtlas&&(this.sdfAtlas=null),this.internals.nodeDataTexture&&(this.internals.nodeDataTexture.kill(),this.internals.nodeDataTexture=null),this.internals.nodeFrameTexture&&(this.internals.nodeFrameTexture.kill(),this.internals.nodeFrameTexture=null),this.internals.edgeDataTexture&&(this.internals.edgeDataTexture.kill(),this.internals.edgeDataTexture=null),this.internals.edgeFrameTexture&&(this.internals.edgeFrameTexture.kill(),this.internals.edgeFrameTexture=null),this.webGLContext){var f;(f=this.webGLContext.getExtension("WEBGL_lose_context"))===null||f===void 0||f.loseContext(),this.webGLContext=null}(s=this.gestureHint)===null||s===void 0||s.kill(),this.gestureHint=null,this.mouseLayer.remove();for(var h in this.extraElements)this.extraElements[h].remove();this.extraElements={}}},{key:"scaleSize",value:function(){var e=arguments.length>0&&arguments[0]!==void 0?arguments[0]:1,r=arguments.length>1&&arguments[1]!==void 0?arguments[1]:this.camera.ratio;return e/this.internals.settings.zoomToSizeRatioFunction(r)*(this.getSetting("itemSizesReference")==="positions"?r*this.graphToViewportRatio:1)}},{key:"getStageCanvas",value:function(){return this.stageCanvas}},{key:"getMouseLayer",value:function(){return this.mouseLayer}}])}(un),Ui=Gd;var Gc=Me(Ke());function Hi(a){var n=a??{},t=n.lengthRatio,e=t===void 0?5:t,r=n.widthRatio,i=r===void 0?4:r,o=n.margin,s=o===void 0?0:o,l=`
// Arrow SDF: triangle with base at x=0, tip at x=lengthRatio
// uv.x: 0 (base) to lengthRatio (tip), uv.y: [-halfW, +halfW]
// Returns signed distance (negative inside, positive outside)
float extremity_arrow(vec2 uv, float lengthRatio, float widthRatio) {
  float x = uv.x;
  float y = abs(uv.y);
  float halfW = widthRatio * 0.5;

  // Past the tip: euclidean distance to tip point
  if (x > lengthRatio) {
    return length(vec2(x - lengthRatio, y));
  }

  // Back edge: signed distance to x=0 line
  float backDist = -x;

  // Side edge: signed distance to sloped triangle edge
  float clampedX = max(0.0, x);
  float maxY = halfW * (1.0 - clampedX / lengthRatio);
  float sideDist = y - maxY;

  // Convex shape SDF = max of half-plane distances
  return max(backDist, sideDist);
}
`;return{name:"arrow",glsl:l,length:e,widthFactor:i,margin:s,uniforms:[],attributes:[]}}return no(zd);})();
