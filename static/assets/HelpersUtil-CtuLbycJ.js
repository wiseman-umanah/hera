import{Pt as e,S as t,at as n,g as r,gt as i,h as a,u as o,v as s}from"./index-CcPesAcv.js";import{s as c}from"./wui-text-BVRBh7MS.js";import{t as l}from"./ConstantsUtil-C1qdKpER.js";var u=r`
  :host {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: ${({spacing:e})=>e[1]};
    text-transform: uppercase;
    white-space: nowrap;
  }

  :host([data-variant='accent']) {
    background-color: ${({tokens:e})=>e.core.foregroundAccent010};
    color: ${({tokens:e})=>e.core.textAccentPrimary};
  }

  :host([data-variant='info']) {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    color: ${({tokens:e})=>e.theme.textSecondary};
  }

  :host([data-variant='success']) {
    background-color: ${({tokens:e})=>e.core.backgroundSuccess};
    color: ${({tokens:e})=>e.core.textSuccess};
  }

  :host([data-variant='warning']) {
    background-color: ${({tokens:e})=>e.core.backgroundWarning};
    color: ${({tokens:e})=>e.core.textWarning};
  }

  :host([data-variant='error']) {
    background-color: ${({tokens:e})=>e.core.backgroundError};
    color: ${({tokens:e})=>e.core.textError};
  }

  :host([data-variant='certified']) {
    background-color: ${({tokens:e})=>e.theme.foregroundSecondary};
    color: ${({tokens:e})=>e.theme.textSecondary};
  }

  :host([data-size='md']) {
    height: 30px;
    padding: 0 ${({spacing:e})=>e[2]};
    border-radius: ${({borderRadius:e})=>e[2]};
  }

  :host([data-size='sm']) {
    height: 20px;
    padding: 0 ${({spacing:e})=>e[1]};
    border-radius: ${({borderRadius:e})=>e[1]};
  }
`,d=function(e,t,n,r){var i=arguments.length,a=i<3?t:r===null?r=Object.getOwnPropertyDescriptor(t,n):r,o;if(typeof Reflect==`object`&&typeof Reflect.decorate==`function`)a=Reflect.decorate(e,t,n,r);else for(var s=e.length-1;s>=0;s--)(o=e[s])&&(a=(i<3?o(a):i>3?o(t,n,a):o(t,n))||a);return i>3&&a&&Object.defineProperty(t,n,a),a},f=class extends s{constructor(){super(...arguments),this.variant=`accent`,this.size=`md`,this.icon=void 0}render(){this.dataset.variant=this.variant,this.dataset.size=this.size;let e=this.size===`md`?`md-medium`:`sm-medium`,n=this.size===`md`?`md`:`sm`;return t`
      ${this.icon?t`<wui-icon size=${n} name=${this.icon}></wui-icon>`:null}
      <wui-text
        display="inline"
        data-variant=${this.variant}
        variant=${e}
        color="inherit"
      >
        <slot></slot>
      </wui-text>
    `}};f.styles=[a,u],d([c()],f.prototype,`variant`,void 0),d([c()],f.prototype,`size`,void 0),d([c()],f.prototype,`icon`,void 0),f=d([o(`wui-tag`)],f);var p={getTabsByNamespace(t){return t&&t===e.CHAIN.EVM?i.state.remoteFeatures?.activity===!1?l.ACCOUNT_TABS.filter(e=>e.label!==`Activity`):l.ACCOUNT_TABS:[]},isValidReownName(e){return/^[a-zA-Z0-9]+$/gu.test(e)},isValidEmail(e){return/^[^\s@]+@[^\s@]+\.[^\s@]+$/gu.test(e)},validateReownName(e){return e.replace(/\^/gu,``).toLowerCase().replace(/[^a-zA-Z0-9]/gu,``)},hasFooter(){let e=n.state.view;if(l.VIEWS_WITH_LEGAL_FOOTER.includes(e)){let{termsConditionsUrl:e,privacyPolicyUrl:t}=i.state,n=i.state.features?.legalCheckbox;return!(!e&&!t||n)}return l.VIEWS_WITH_DEFAULT_FOOTER.includes(e)}};export{p as t};