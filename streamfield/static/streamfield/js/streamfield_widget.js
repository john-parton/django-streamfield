(function(w, $) {
  /* wtf does this do? */
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
      var popup_size = JSON.parse(text_area.dataset.popup_size);

      var config = text_area.dataset;
      var base_admin_url = config.base_admin_url;

      console.log(config.delete_url);

      var data = {
        stream: JSON.parse(initial_data), // [{model_name: ..., id: ...}, ...]
        model_info: JSON.parse(model_list_info), // {'model_name': model.__doc__}
        blocks: {}, // save content of all instances
        show_help: false,
        show_add_block: false,
        to_delete: [] // blocks that will be removed from db
      };

      var app = new Vue({
        el: app_node,
        data: data,
        beforeMount: function() {
          // update stream objects list
          // and store all blocks

          data.stream.forEach(block => {
            block.object_id.forEach(
              block_id => this.updateBlock(block.unique_id, block_id)
            )
          });

          // delete removed instances from db when form submit
          if ( delete_blocks_from_db ) {
            // TODO Remove jquery
            $('input[type="submit"]', text_area.closest('form')).on('click', function (e) {
              if ( !app.to_delete.length ) return;

              e.preventDefault();

              var all_requests = [];

              // could map directly in Promise.all
              app.to_delete.forEach(({content_type_id, object_id}) => {
                all_requests.push(app.deleteAction(content_type_id, object_id))  // why app and not this?
              });

              Promise.all(all_requests).then(function(){
                app.to_delete = [];
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

          model_title: function (block) {
            return this.model_info[block.content_type_id].verbose_name;
          },

          model_name: function (block) {
            return this.model_info[block.content_type_id].model_name;
          },

          instance_unique_id: (block, instance_id) => block.content_type_id + ":" + instance_id,

          create_unique_hash: () => Math.random().toString(36).substring(7),

          hasOptions: function (block) {
            return Object.keys(
                this.model_info[block.content_type_id].options
            ).length > 0;
          },

          block_admin_url: function (block) {
            return this.model_info[block.content_type_id].admin_url;
          },

          get_change_model_link: function(block, instance_id) {
            // Fix this to actually use URLParams
            return `${ this.block_admin_url(block) }${ instance_id }/change/?_popup=1&block_id=${ block.unique_id }&instance_id=${ instance_id }&app_id=${ app_node.id }`
          },

          get_add_model_link: function (block) {
            // Fix this to actually use URLParams
            return this.block_admin_url(block) +
              'add/?_popup=1&block_id=' + block.unique_id +
              '&app_id=' + app_node.id;
          },

          getBlockContent: function(block, item_id) {
            return this.blocks[this.instance_unique_id(block, item_id)];
          },

          updateBlock: function (block_unique_id, instance_id) {
            // Ensure always an integer... better place to put this?
            instance_id = parseInt(instance_id);

            var block = this.stream.find(block => block['unique_id'] == block_unique_id);


            // change block content
            ax.get(
              config.render_url, {
                'params': {
                  content_type_id: block.content_type_id,
                  object_id: instance_id
                }
              }
            ).then(
              response => app.$set(app.blocks, app.instance_unique_id(block, instance_id), response.data)
            );

            if (block.object_id.indexOf(instance_id) == -1) {
              block.object_id.push(instance_id);
            }
          },

          deleteBlock: function (block_unique_id) {
            var index = this.stream.findIndex(block => block['unique_id'] == block_unique_id);

            if (index == -1) {
              return;
            }

            var block = this.stream[index];

            if (confirm(`"${ this.model_title(block) }" - ${ stream_texts['deleteBlock'] }`)) {
              this.stream.splice(index, 1);
              // prepare to remove from db

              // map/extend would work too
              block.object_id.forEach(
                object_id => this.to_delete.push({
                  content_type_id: block.content_type_id,
                  object_id: object_id
                })
              )

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
              block.object_id.splice(
                block.object_id.indexOf(instance_id), 1
              );

              // prepare to remove from db
              this.to_delete.push({
                content_type_id: block.content_type_id,
                object_id: instance_id
              });
            }
          },

          // TODO Test this better
          // TODO Consider /streamfield/delete/ with query params instead
          // This is rather dangerous -- deletes things with minimal confirmation
          deleteAction: (content_type_id, object_id) => ax.delete(
            config.delete_url, {
              'params': {
                content_type_id: content_type_id,
                object_id: object_id
              }
            }
          ),

          addNewBlock: function (block, content_type_id) {
            // Sometimes a string for some reason?
            content_type_id = parseInt(content_type_id);

            var options = {};

            // Don't fully understand this
            Object.entries(this.model_info[content_type_id].options).forEach(
              ([key, option]) => {
                  app.$set(options, key, option.default);
              }
            );

            this.stream.push({
              unique_id: this.create_unique_hash(),
              content_type_id: content_type_id,
              options: options,
              object_id: []
            });

            this.show_add_block = false;
          },

          openPopup: ({target}) => {
            w.open(
              target.href,
              id_to_windowname(target.id.replace(/^(change|add|delete)_/, '')),
              `height=${ popup_size[1]},width=${ popup_size[0] },resizable=yes,scrollbars=yes`
            ).focus();

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
