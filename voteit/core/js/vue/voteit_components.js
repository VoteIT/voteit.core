Vue.component('user-table', {
    data: function() {
        return {
            isModerator: this.$root.isModerator,
            users: this.$root.users,
            itemsPerPage: 25,
            currentPage: 0,
            textFilter: ''
        };
    },
    props: ['src', 'roleApi', 'bulkWarning', 'currentUser', 'textFilterFields'],
    mounted: function() {
        if (!this.users.length) {
            do_request(this.src)
            .done(function(response) {
                for (i=0; i<response.results.length; i++) {
                    response.results[i].selected = false;
                }
                this.users = response.results;
                this.sortUsers();
            }.bind(this))
        }
    },
    methods: {
        roleCount: function(role) {
            return this.users.filter(function(user) {
                return user[role];
            }).length;
        },
        setUsersRole(users, role, state) {
            do_request(this.rolesApi, {
                data: {
                    userid: userid,
                    role: role,
                    state: state
                },
                method: 'POST'
            })
            .done(function(response) {
                for (i=0; i<users.length; i++) {
                    users[i][role] = state;
                }
            });
        },
        setAllRole(role, state) {
            if (confirm(this.bulkWarning)) {
                do_request(this.roleApi, {
                    data: {
                        all_users: true,
                        role: role,
                        state: state
                    },
                    method: 'POST'
                })
                .done(function(response) {
                    for (i=0; i<this.users.length; i++) {
                        this.users[i][role] = state;
                    }
                }.bind(this));
            }
        },
        toggleRole: function(user, role) {
            var state = !user[role];
            do_request(this.roleApi, {
                data: {
                    userid: user.userid,
                    role: role,
                    state: state
                },
                method: 'POST'
            })
            .done(function(response) {
                user[role] = state;
            });
        },
        toggleSelectAll: function() {
            var allSelected = this.allSelected;
            for (i=0; i<this.users.length; i++) {
                this.users[i].selected = !allSelected;
            }
        },
        toggleSelected: function(user) {
            user.selected = !user.selected;
        },
        getPage: function(id) {
            this.currentPage = id;
        },
        sortUsers: function(order) {
            this.users.sort(function(user_a, user_b) {
                if (!order) {
                    return user_a.userid !== this.currentUser;
                } else if (typeof user_a[order] === 'boolean') {
                    return user_a[order] < user_b[order];
                } else {
                    return user_a[order] > user_b[order];
                }
            }.bind(this));
        }
    },
    computed: {
        allSelected: function() {
            for (i=0; i<this.users.length; i++) {
                if (!this.users[i].selected) return false;
            }
            return true;
        },
        anySelected: function() {
            for (i=0; i<this.users.length; i++) {
                if (this.users[i].selected) return true;
            }
            return false;
        },
        selectedUsers: function() {
            return this.users.filter(function(user) {
                return user.selected;
            });
        },
        displayUsers: function() {
            var start = this.currentPage * this.itemsPerPage;
            var end = start + this.itemsPerPage;
            return this.filteredUsers.slice(start, end);
        },
        pages: function() {
          var users = this.filteredUsers;
          if (users.length <= this.itemsPerPage) return;
          var pages = [];
          var endPage = Math.ceil(users.length / this.itemsPerPage) - 1;
          var sliceStart = this.currentPage - 3;
          var sliceEnd = this.currentPage + 3;
          if (sliceStart < 0 !== sliceEnd > endPage) {  // Only one is off
            if (sliceStart < 0) {  // Start is off
              sliceEnd = 6;
            } else {  // End is off
              sliceStart = endPage - 6;
            }
          }
          // Make sure nothing is off after this.
          sliceStart = Math.max(sliceStart, 0);
          sliceEnd = Math.min(sliceEnd, endPage);
          if (typeof users.length !== 'undefined') {
            if (sliceStart > 0) {
              pages.push({
                text: '«',
                id: 0
              });
            }
            for (page=sliceStart; page<=sliceEnd; page++) {
              var start = (page * this.itemsPerPage) + 1;
              var end = Math.min((page * this.itemsPerPage) + this.itemsPerPage, users.length);
              pages.push({
                text: (start === end) ? start : start + ' - ' + end,
                active: page === this.currentPage,
                id: page
              });
            }
            if (sliceEnd < endPage) {
              pages.push({
                text: '»',
                id: endPage
              });
            }
          }
          return pages;
        },
        filteredUsers: function() {
            if (this.textFilter) {
                return this.users.filter(function(user) {
                    var fields = this.textFilterFields.split(/\s+/);
                    var searches = this.textFilter.split(/\s+/);
                    for (s=0; s<searches.length; s++) {
                        var search = searches[s].toLowerCase();
                        var match = false;
                        for (f=0; f<fields.length; f++) {
                            var value = user[fields[f]];
                            if (value && value.toLowerCase().indexOf(search) !== -1) {
                                match = true;
                                break;
                            }
                        }
                        if (!match) return false;
                    }
                    return true;
                }.bind(this));
            }
            return this.users;
        }
    },
    watch: {
        textFilter: function(val) {
            this.currentPage = 0;
        }
    }
});

$(function() {
    var voteITMeeting = new Vue({
        data: {
            users: []
        },
        el: '#content',
        props: ['isModerator'],
        created: function() {
            this.isModerator = $('body').hasClass('is_moderator');
        },
    });
});
