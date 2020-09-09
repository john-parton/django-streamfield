(function(w, $) {
  function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
  }

  function onReady() {

    var csrftoken = Cookies.get('csrftoken');
    var ax = axios.create({
      headers: {"X-CSRFToken": csrftoken}
    });

    w.streamapps = {};

    document.querySelectorAll('.streamfield_app').forEach(app_node => {
      var text_area = app_node.querySelector('textarea');
      var initial_data = text_area.innerHTML;
      var model_list_info = text_area.getAttribute('model_list_info');
      var delete_blocks_from_db = Boolean(text_area.hasAttribute('delete_blocks_from_db'));
      var base_admin_url = text_area.getAttribute('base_admin_url');
      var popup_size = JSON.parse(text_area.dataset.popup_size);

      var data = {
        stream: JSON.parse(initial_data), // [{model_name: ..., id: ...}, ...]
        model_info: JSON.parse(model_list_info), // {'model_name': model.__doc__}
        blocks: {}, // save content of all instances
        show_help: false,
        show_add_block: false,
        will_removed: [] // blocks that will be removed from db
      };

      console.log(data.model_info);

      var app = new Vue({
        el: app_node,
        data: data,
        beforeMount: function() {
          // update stream objects list
          // and store all blocks

          data.stream.forEach(block => {
            if ( this.isAbstract(block) ) {
              this.updateAbstractBlock(block.unique_id);
            } else {
              block.object_id.forEach(
                block_id => this.updateBlock(block.unique_id, block_id)
              )
            }
          });

          // delete removed instances from db when form submit
          if ( delete_blocks_from_db ) {
            $('input[type="submit"]', text_area.closest('form')).on('click', function(e){
              if ( !app.will_removed.length ) return;

              e.preventDefault();

              var all_requests = [];

              for (var i = app.will_removed.length - 1; i >= 0; i--) {
                if ( app.will_removed[i].id != -1 ) {

                  // for array
                  if ( Array.isArray(app.will_removed[i].object_id) ) {
                    var ids = app.will_removed[i].object_id;
                    for (var j = ids.length - 1; j >= 0; j--) {
                      all_requests.push(app.deleteAction(app.will_removed[i], ids[j], i));
                    }
                  // for one
                  } else {
                    all_requests.push(app.deleteAction(app.will_removed[i], app.will_removed[i].object_id, i));
                  }
                }
              }

              Promise.all(all_requests).then(function(){
                app.will_removed = [];
                $(e.target).trigger('click');
              });

            }); // EventListener
          }

        },
        methods: {
          isArray: obj => Array.isArray(obj),

          asList: function (block) {
            return this.model_info[block.content_type_id].as_list;
          },

          isAbstract: function (block) {
            return this.model_info[block.content_type_id].abstract;
          },

          model_title: function (block) {
            var title = '...';
            if (this.model_info[block.content_type_id]) {
              title = this.model_info[block.content_type_id].model_doc;
            }
            return title;
          },

          model_name: function (block) {
            return this.model_info[block.content_type_id].model_name;
          },

          instance_unique_id: (block, instance_id) => block.content_type_id + ":" + instance_id,

          create_unique_hash: () => Math.random().toString(36).substring(7),

          block_admin_url: function (block) {
            return base_admin_url + 'streamblocks/' + this.model_name(block) + '/';
          },

          instance_admin_render_url: function (block, instance_id) {
            return '/streamfield/admin-instance/' + this.model_name(block) + '/' + instance_id;
          },

          abstract_block_render_url: function (block) {
            return '/streamfield/abstract-block/' + this.model_name(block) + '/';
          },

          get_change_model_link: function(block, instance_id) {
            return this.block_admin_url(block) + instance_id +
              '/change/?_popup=1&block_id=' + block.unique_id +
              '&instance_id=' + instance_id +
              '&app_id=' + app_node.id;
          },

          get_add_model_link: function (block) {
            return this.block_admin_url(block) +
              'add/?_popup=1&block_id=' + block.unique_id +
              '&app_id=' + app_node.id;
          },

          getBlockContent: function(block, item_id) {
            return this.blocks[this.instance_unique_id(block, item_id)];
          },

          getAbstractBlockContent: function(block) {
            return this.blocks[block.content_type_id];
          },

          updateAbstractBlock(block_unique_id) {
            var block = this.stream.find(block => block['unique_id'] == block_unique_id);

            // change block content
            ax.get(this.abstract_block_render_url(block)).then(
              response => app.$set(app.blocks, block.content_type_id, response.data)
            );
          },

          updateBlock: function (block_unique_id, instance_id) {
            // Ensure always an integer... better place to put this?
            instance_id = parseInt(instance_id);

            var block = this.stream.find(block => block['unique_id'] == block_unique_id);

            // change block content
            ax.get(
              this.instance_admin_render_url(block, instance_id)
            ).then(
              response => app.$set(app.blocks, app.instance_unique_id(block, instance_id), response.data)
            );

            if (block.object_id.indexOf(instance_id) == -1) {
              block.object_id.push(instance_id);
            }
          },

          deleteBlock: function(block_unique_id) {
            var index = this.stream.findIndex(block => block['unique_id'] == unique_id);

            if (index == -1) {
              return;
            }

            var block = this.stream[index];

            if (confirm('"' + this.model_title(block) + '" - ' + stream_texts['deleteBlock'])) {
              this.stream.splice(index, 1);
              // prepare to remove from db
              if ( !this.isAbstract(block) ) {
                this.will_removed.push(block);
              }
            }
          },

          deleteInstance: function(block_unique_id, instance_id) {
            var index = this.stream.findIndex(block => block['unique_id'] == unique_id);

            if (index == -1) {
              return;
            }

            var block = this.stream[index];

            if (confirm(stream_texts['deleteInstance'])) {
              // remove from block id
              block.id.splice(block.id.indexOf(instance_id), 1);

              // prepare to remove from db
              this.will_removed.push({
                content_type_id: block.content_type_id,
                object_id: instance_id
              });
            }
          },

          deleteAction: function(block, id, idx) {
            return ax.delete(
              '/streamfield/admin-instance/' + app.model_name(block) + '/' + id + '/delete/'
            )
          },

          addNewBlock: function(block, content_type_id) {
            content_type_id = parseInt(content_type_id);

            var options = {};
            var new_block;

            Object.entries(this.model_info[content_type_id].options).forEach(
              ([key, option]) => app.$set(options, key, option.default)
            );

            new_block = {
              unique_id: this.create_unique_hash(),
              content_type_id: content_type_id,
              options: options,
              object_id: []
            };

            this.stream.push(new_block);
            this.show_add_block = false;
          },

          openPopup: function(e){
            var triggeringLink = e.target;
            var name = id_to_windowname(triggeringLink.id.replace(/^(change|add|delete)_/, ''));
            var href = triggeringLink.href;
            var win = w.open(href, name, 'height=' + popup_size[1] + ',width=' + popup_size[0] + ',resizable=yes,scrollbars=yes');
            win.focus();
            return false;
          }
        },

        computed: {
          textarea: function(){
            return JSON.stringify(this.stream.map(function(i){
              // return only fields that in initial data
              return {
                unique_id: i.unique_id,
                content_type_id: i.content_type_id,
                object_id: i.object_id,
                options: i.options
              };
            }));
          }
        }
      });

      w.streamapps[app_node.id] = app;
    });
  };

  w.addEventListener('DOMContentLoaded', function(event) {
    onReady();
  });

})(window, django.jQuery);
