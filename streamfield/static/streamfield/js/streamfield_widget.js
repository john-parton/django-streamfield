(function (w) {
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

      var textarea = app_node.querySelector('textarea');
      var config = textarea.dataset;

      var delete_blocks_from_db = config.deleteBlocksFromDb !== undefined;

      var popup_size = JSON.parse(config.popupSize);

      var data = {
        stream: JSON.parse(textarea.innerHTML), // [{model_name: ..., id: ...}, ...]
        model_metadata: JSON.parse(config.modelMetadata), // {'model_name': model.__doc__}
        blocks: {}, // save content of all instances
        show_help: config.showHelpText !== undefined,
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
          // this could be globally delgated? Then it wouldn't need to be in beforeMount
          if ( delete_blocks_from_db ) {
            document.querySelectorAll('#page_form input[type="submit"]').forEach(
              node => node.addEventListener('click', (e) => {
                if (app.to_delete.length > 0) {
                  e.preventDefault();

                  // This is rather dangerous -- deletes things with minimal confirmation
                  Promise.all(
                    app.to_delete.map(
                      params => ax.delete(
                        config.delete_url, {
                          'params': params
                        }
                      )
                    )
                  ).then(() => {
                    app.to_delete = [];
                    node.click();
                  });
                }
              })
            );
          }
        },

        methods: {
          isArray: obj => Array.isArray(obj),

          getMetadata: function (block, key) {
            return this.model_metadata[block.content_type_id][key];
          },

          instance_unique_id: (block, instance_id) => `${ block.content_type_id }:${ instance_id }`,

          create_unique_hash: () => Math.random().toString(36).substring(7),

          hasOptions: function (block) {
            return Object.keys(
                this.getMetadata(block, 'options')
            ).length > 0;
          },

          get_change_model_link: function (block, instance_id) {
            // Fix this to actually use URLParams
            return `${ this.getMetadata(block, 'admin_url') }${ instance_id }/change/?_popup=1&app_id=${ app_node.id }&block_id=${ block.unique_id }&instance_id=${ instance_id }`;
          },

          get_add_model_link: function (block) {
            // Fix this to actually use URLParams
            return `${ this.getMetadata(block, 'admin_url') }add/?_popup=1&app_id=${ app_node.id }&block_id=${ block.unique_id }`;
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

            if (confirm(`"${ this.getMetadata(block, 'verbose_name') }" - ${ stream_texts['deleteBlock'] }`)) {
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

          addNewBlock: function (block, content_type_id) {
            // Sometimes a string for some reason?
            content_type_id = parseInt(content_type_id);

            var options = {};

            // Don't fully understand this
            Object.entries(
              this.getMetadata(block, 'options')
            ).forEach(
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

            // TODO If the block doesn't have as_list, then why not directly open the popup right away?
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
          textarea: function() {
            return JSON.stringify(this.stream);
          }
        }
      });

      w.streamapps[app_node.id] = app;
    });
  };

  w.addEventListener('DOMContentLoaded', function(event) {
    onReady();
  });

})(window);
