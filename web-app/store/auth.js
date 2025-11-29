import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core";

const mode = process.env.NODE_ENV;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    auth: useLocalStorage("auth", {
      token: null,
      refreshToken: null,
    }),

    user: null,
    needsLogin: false,
    publicKey: null,
  }),

  actions: {
    async isAuthorized(user) {
      return (
        user.roles.includes("admin") ||
        user.roles.includes("editor") ||
        !user.restricted
      );
    },

    async getUser() {
      let $api = useNuxtApp().$api;

      try {
        // console.log("Access Token", this.auth.token)
        let user = await $api("/users/me", {
          headers: { Authorization: "Bearer " + this.auth.token },
        });
        this.user = user;
        // console.log("set user", this.user);
        this.needsLogin = !(await this.isAuthorized(this.user));
        return this.user;
      } catch (e) {
        if (e.response) {
          if (e.response.status == 401) {
            // console.log("data", e.response.data);
            // console.log("Refresh token", this.auth.refreshToken);
            if (this.auth.refreshToken) {
              try {
                let res = await $api("/users/me/token?setCookie=true", {
                  headers: {
                    Authorization: "Bearer " + this.auth.refreshToken,
                  },
                });

                this.auth.token = res.access_token;
                this.auth.refreshToken = res.refresh_token;
                this.user = res.user;
                this.needsLogin = !(await this.isAuthorized(this.user));
                return this.user;
              } catch (e) {
                this.auth.refreshToken = null;
                this.auth.token = null;
                this.needsLogin = true;
              }
            } else {
              this.needsLogin = true;
            }
          }
        }
      }

      return null;
    },

    async logout() {
      let $api = useNuxtApp().$api;

      this.auth.token = null;
      this.auth.refreshToken = null;
      this.user = null;
      this.needsLogin = true;

      await $api("/logout", {
        method: "POST",
      });

      navigateTo("/signin");
    },

    async beginResetPassword(email) {
      let $api = useNuxtApp().$api;
      await $api("/password-reset", {
        method: "GET",
        query: { email: email },
      });
    },

    async resetPassword(email, code, password) {
      let $api = useNuxtApp().$api;
      await $api("/password-reset", {
        method: "POST",
        body: {
          email: email,
          password: password,
          code: code,
        },
      });
    },

    async login(email, password) {
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      let $api = useNuxtApp().$api;
      let res = await $api("/login?setCookie=true", {
        method: "POST",
        body: params,
      });
      const isAuthorized = await this.isAuthorized(res.user);
      if (!isAuthorized) {
        throw new Error("Don't have required permissions");
      }
      this.auth.token = res.access_token;
      this.auth.refreshToken = res.refresh_token;
      return await this.getUser();
    },

    async setSsoCreds(accessToken, refreshToken) {
      this.auth.token = accessToken;
      this.auth.refreshToken = refreshToken;
      return await this.getUser();
    },
  },
});
