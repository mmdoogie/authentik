import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CoreApi, User } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG, tenant } from "../../api/Config";
import { uiConfig } from "../../common/config";
import "../../elements/buttons/ActionButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import { MessageLevel } from "../../elements/messages/Message";
import { showMessage } from "../../elements/messages/MessageContainer";
import { getURLParam, updateURLParams } from "../../elements/router/RouteMatch";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import { first } from "../../utils";
import "./ServiceAccountForm";
import "./UserActiveForm";
import "./UserForm";
import "./UserResetEmailForm";

@customElement("ak-user-list")
export class UserListPage extends TablePage<User> {
    expandable = true;
    checkbox = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Users`;
    }
    pageDescription(): string {
        return "";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-user";
    }

    @property()
    order = "last_login";

    @property({ type: Boolean })
    hideServiceAccounts = getURLParam<boolean>("hideServiceAccounts", true);

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    async apiEndpoint(page: number): Promise<AKResponse<User>> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            attributes: this.hideServiceAccounts
                ? JSON.stringify({
                      "goauthentik.io/user/service-account__isnull": "true",
                  })
                : undefined,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "username"),
            new TableColumn(t`Active`, "active"),
            new TableColumn(t`Last login`, "last_login"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html` <ak-forms-delete-bulk
            objectLabel=${t`User(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: User) => {
                return [
                    { key: t`Username`, value: item.username },
                    { key: t`ID`, value: item.pk.toString() },
                ];
            }}
            .usedBy=${(item: User) => {
                return new CoreApi(DEFAULT_CONFIG).coreUsersUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: User) => {
                return new CoreApi(DEFAULT_CONFIG).coreUsersDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: User): TemplateResult[] {
        return [
            html`<a href="#/identity/users/${item.pk}">
                <div>${item.username}</div>
                <small>${item.name}</small>
            </a>`,
            html`${item.isActive ? t`Yes` : t`No`}`,
            html`${first(item.lastLogin?.toLocaleString(), t`-`)}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update User`} </span>
                    <ak-user-form slot="form" .instancePk=${item.pk}> </ak-user-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                <a class="pf-c-button pf-m-tertiary" href="${`/-/impersonation/${item.pk}/`}">
                    ${t`Impersonate`}
                </a>`,
        ];
    }

    renderExpanded(item: User): TemplateResult {
        return html`<td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <dl class="pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`User status`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${item.isActive ? t`Active` : t`Inactive`}
                                </div>
                                <div class="pf-c-description-list__text">
                                    ${item.isSuperuser ? t`Superuser` : t`Regular user`}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Change status`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    <ak-user-active-form
                                        .obj=${item}
                                        objectLabel=${t`User`}
                                        .delete=${() => {
                                            return new CoreApi(
                                                DEFAULT_CONFIG,
                                            ).coreUsersPartialUpdate({
                                                id: item.pk || 0,
                                                patchedUserRequest: {
                                                    isActive: !item.isActive,
                                                },
                                            });
                                        }}
                                    >
                                        <button slot="trigger" class="pf-c-button pf-m-warning">
                                            ${item.isActive ? t`Deactivate` : t`Activate`}
                                        </button>
                                    </ak-user-active-form>
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text">${t`Recovery`}</span>
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${until(
                                        tenant().then((tenant) => {
                                            if (!tenant.flowRecovery) {
                                                return html`
                                                    <p>
                                                        ${t`To directly reset a user's password, configure a recovery flow on the currently active tenant.`}
                                                    </p>
                                                `;
                                            }
                                            return html`
                                                <ak-action-button
                                                    .apiRequest=${() => {
                                                        return new CoreApi(DEFAULT_CONFIG)
                                                            .coreUsersRecoveryRetrieve({
                                                                id: item.pk || 0,
                                                            })
                                                            .then((rec) => {
                                                                showMessage({
                                                                    level: MessageLevel.success,
                                                                    message: t`Successfully generated recovery link`,
                                                                    description: rec.link,
                                                                });
                                                            })
                                                            .catch((ex: Response) => {
                                                                ex.json().then(() => {
                                                                    showMessage({
                                                                        level: MessageLevel.error,
                                                                        message: t`No recovery flow is configured.`,
                                                                    });
                                                                });
                                                            });
                                                    }}
                                                >
                                                    ${t`Copy recovery link`}
                                                </ak-action-button>
                                                ${item.email
                                                    ? html`<ak-forms-modal
                                                          .closeAfterSuccessfulSubmit=${false}
                                                      >
                                                          <span slot="submit">
                                                              ${t`Send link`}
                                                          </span>
                                                          <span slot="header">
                                                              ${t`Send recovery link to user`}
                                                          </span>
                                                          <ak-user-reset-email-form
                                                              slot="form"
                                                              .user=${item}
                                                          >
                                                          </ak-user-reset-email-form>
                                                          <button
                                                              slot="trigger"
                                                              class="pf-c-button pf-m-secondary"
                                                          >
                                                              ${t`Email recovery link`}
                                                          </button>
                                                      </ak-forms-modal>`
                                                    : html`<span
                                                          >${t`Recovery link cannot be emailed, user has no email address saved.`}</span
                                                      >`}
                                            `;
                                        }),
                                    )}
                                </div>
                            </dd>
                        </div>
                    </dl>
                </div>
            </td>
            <td></td>
            <td></td>`;
    }

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create User`} </span>
                <ak-user-form slot="form"> </ak-user-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            <ak-forms-modal .closeAfterSuccessfulSubmit=${false} .cancelText=${t`Close`}>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Service account`} </span>
                <ak-user-service-account slot="form"> </ak-user-service-account>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Create Service account`}
                </button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }

    renderToolbarAfter(): TemplateResult {
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group">
                        <div class="pf-c-check">
                            <input
                                class="pf-c-check__input"
                                type="checkbox"
                                id="hide-service-accounts"
                                name="hide-service-accounts"
                                ?checked=${this.hideServiceAccounts}
                                @change=${() => {
                                    this.hideServiceAccounts = !this.hideServiceAccounts;
                                    this.page = 1;
                                    this.fetch();
                                    updateURLParams({
                                        hideServiceAccounts: this.hideServiceAccounts,
                                    });
                                }}
                            />
                            <label class="pf-c-check__label" for="hide-service-accounts">
                                ${t`Hide service-accounts`}
                            </label>
                        </div>
                    </div>
                </div>
            </div>`;
    }
}
