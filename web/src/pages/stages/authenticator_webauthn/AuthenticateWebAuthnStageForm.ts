import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { AuthenticateWebAuthnStage, StagesApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-authenticator-webauthn-form")
export class AuthenticateWebAuthnStageForm extends ModelForm<AuthenticateWebAuthnStage, string> {
    loadInstance(pk: string): Promise<AuthenticateWebAuthnStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: AuthenticateWebAuthnStage): Promise<AuthenticateWebAuthnStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnUpdate({
                stageUuid: this.instance.pk || "",
                authenticateWebAuthnStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorWebauthnCreate({
                authenticateWebAuthnStageRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to configure a WebAutnn authenticator (i.e. Yubikey, FaceID/Windows Hello).`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
