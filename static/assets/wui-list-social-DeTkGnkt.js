import{Ct as e,Pt as t,Rt as n,S as r,W as i,at as a,g as o,h as s,ht as c,lt as l,p as u,rt as d,u as f,v as p,wt as m}from"./index-CcPesAcv.js";import{s as h}from"./wui-text-BVRBh7MS.js";import{t as g}from"./if-defined-Dzc7La58.js";function _(){try{return e.returnOpenHref(`${t.SECURE_SITE_SDK_ORIGIN}/loading`,`popupWindow`,`width=600,height=800,scrollbars=yes`)}catch{throw Error(`Could not open social popup`)}}async function v(){a.push(`ConnectingFarcaster`);let e=d.getAuthConnector();if(e&&!i.getAccountData()?.farcasterUrl)try{let{url:t}=await e.provider.getFarcasterUri();i.setAccountProp(`farcasterUrl`,t,i.state.activeChain)}catch(e){a.goBack(),c.showError(e)}}async function y(t){a.push(`ConnectingSocial`);let r=d.getAuthConnector(),o=null;try{let a=setTimeout(()=>{throw Error(`Social login timed out. Please try again.`)},45e3);if(r&&t){if(e.isTelegram()||(o=_()),o)i.setAccountProp(`socialWindow`,n(o),i.state.activeChain);else if(!e.isTelegram())throw Error(`Could not create social popup`);let{uri:s}=await r.provider.getSocialRedirectUri({provider:t});if(!s)throw o?.close(),Error(`Could not fetch the social redirect uri`);if(o&&(o.location.href=s),e.isTelegram()){m.setTelegramSocialProvider(t);let n=e.formatTelegramSocialLoginUrl(s);e.openHref(n,`_top`)}clearTimeout(a)}}catch(n){o?.close();let r=e.parseError(n);c.showError(r),l.sendEvent({type:`track`,event:`SOCIAL_LOGIN_ERROR`,properties:{provider:t,message:r}})}}async function b(e){i.setAccountProp(`socialProvider`,e,i.state.activeChain),l.sendEvent({type:`track`,event:`SOCIAL_LOGIN_STARTED`,properties:{provider:e}}),e===`farcaster`?await v():await y(e)}var x=o`
  :host {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 40px;
    height: 40px;
    border-radius: ${({borderRadius:e})=>e[20]};
    overflow: hidden;
  }

  wui-icon {
    width: 100%;
    height: 100%;
  }
`,S=function(e,t,n,r){var i=arguments.length,a=i<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,n):r,o;if(typeof Reflect==`object`&&typeof Reflect.decorate==`function`)a=Reflect.decorate(e,t,n,r);else for(var s=e.length-1;s>=0;s--)(o=e[s])&&(a=(i<3?o(a):i>3?o(t,n,a):o(t,n))||a);return i>3&&a&&Object.defineProperty(t,n,a),a},C=class extends p{constructor(){super(...arguments),this.logo=`google`}render(){return r`<wui-icon color="inherit" size="inherit" name=${this.logo}></wui-icon> `}};C.styles=[s,x],S([h()],C.prototype,`logo`,void 0),C=S([f(`wui-logo`)],C);var w=o`
  :host {
    width: 100%;
  }

  button {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: ${({spacing:e})=>e[3]};
    width: 100%;
    background-color: transparent;
    border-radius: ${({borderRadius:e})=>e[4]};
  }

  wui-text {
    text-transform: capitalize;
  }

  @media (hover: hover) {
    button:hover:enabled {
      background-color: ${({tokens:e})=>e.theme.foregroundPrimary};
    }
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`,T=function(e,t,n,r){var i=arguments.length,a=i<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,n):r,o;if(typeof Reflect==`object`&&typeof Reflect.decorate==`function`)a=Reflect.decorate(e,t,n,r);else for(var s=e.length-1;s>=0;s--)(o=e[s])&&(a=(i<3?o(a):i>3?o(t,n,a):o(t,n))||a);return i>3&&a&&Object.defineProperty(t,n,a),a},E=class extends p{constructor(){super(...arguments),this.logo=`google`,this.name=`Continue with google`,this.disabled=!1}render(){return r`
      <button ?disabled=${this.disabled} tabindex=${g(this.tabIdx)}>
        <wui-flex gap="2" alignItems="center">
          <wui-image ?boxed=${!0} logo=${this.logo}></wui-image>
          <wui-text variant="lg-regular" color="primary">${this.name}</wui-text>
        </wui-flex>
        <wui-icon name="chevronRight" size="lg" color="default"></wui-icon>
      </button>
    `}};E.styles=[s,u,w],T([h()],E.prototype,`logo`,void 0),T([h()],E.prototype,`name`,void 0),T([h()],E.prototype,`tabIdx`,void 0),T([h({type:Boolean})],E.prototype,`disabled`,void 0),E=T([f(`wui-list-social`)],E);export{b as t};