Date.now = Date.now || function () { return +new Date; };

/*
 *  Models & Collections
 */
Word = Backbone.RelationalModel.extend({
  /* A Word model represents each tokenized word present
   * in the paragraph YPet is attached to. */
  defaults: {
    text: '',
    start: null,
    latest: null,
    neighbor: false,
  }
});

WordList = Backbone.Collection.extend({
  /* Common utils to perform on an array of Word
   * models for house keeping and search */
  model: Word,
  url: '/api/v1/words',
});

Annotation = Backbone.RelationalModel.extend({
  /* Each annotation in the paragraph. An Annotation
   * is composed of an array of Words in order to determine
   * the full text and position which are not
   * explicity set */
  defaults: {
    /* An annotation doesn't exist when removed so
     * we can start them all off at 0 and not need to
     * mix in a null type */
    type: 0,
    text: '',
    start: null,
  },

  sync: function () { return false; },

  relations: [{
    type: 'HasMany',
    key: 'words',

    relatedModel: Word,
    collectionType: WordList,

    reverseRelation: {
      key: 'parentAnnotation',
      includeInJSON: false,
    }
  }],

  toggleType: function () {
    /* Removes (if only 1 Annotation type) or changes
     * the Annotation type when clicked after existing */
    if (this.get('type') == YPet.AnnotationTypes.length - 1) {
      this.destroy();
    } else {
      this.set('type', this.get('type') + 1);
    }
  }
});

AnnotationTypeList = Backbone.Collection.extend({
  /* Very simple collection to store the type of
   * Annotations that the application allows
   * for paragraphs */
  model: Backbone.Model.extend({}),
  url: function () { return false; }
});

AnnotationList = Backbone.Collection.extend({
  /* Utils for the Paragraph Annotations lists
   * collectively */
  model: Annotation,
  url: '/api/v1/annotations',

  sanitizeAnnotation: function (full_str, start) {
    /* Return the cleaned string and the (potentially) new start position */
    var str = _.str.clean(full_str).replace(/^[^a-z\d]*|[^a-z\d]*$/gi, '');
    return { 'text': str, 'start': start + full_str.indexOf(str) };
  },

  initialize: function (options) {
    this.listenTo(this, 'add', function (annotation) {
      var ann = this.sanitizeAnnotation(annotation.get('words').pluck('text').join(' '), annotation.get('words').first().get('start'));
      annotation.set('text', ann.text);
      annotation.set('start', ann.start);
      this.drawAnnotations(annotation);
    });

    this.listenTo(this, 'change:type', function (annotation) {
      this.drawAnnotations(annotation);
    });

    this.listenTo(this, 'remove', function (annotation, collection) {
      /* Must iterate b/c annotation var "words" attribute is
       * empty at this point */
      collection.parentDocument.get('words').each(function (word) {
        word.trigger('highlight', { 'color': '#fff' });
        word.set('neighbor', false);
      });

      collection.each(function (annotation) {
        collection.drawAnnotations(annotation);
      });

    });
  },

  drawAnnotations: function (annotation) {
    var annotation_type = YPet.AnnotationTypes.at(annotation.get('type')),
      words_len = annotation.get('words').length;

    annotation.get('words').each(function (word, word_index) {
      word.trigger('highlight', { 'color': annotation_type.get('color') });
      if (word_index == words_len - 1) { word.set('neighbor', true); }
    });
  },

  add: function (ann) {
    if (ann.get('words').length == 0) { return false; }
    Backbone.Collection.prototype.add.call(this, ann);
  }

});

Paragraph = Backbone.RelationalModel.extend({
  /* Foundational model for tracking everything going
   * on within a Paragraph like Words and Annotations */
  defaults: {
    text: '',
  },

  relations: [{
    type: 'HasMany',
    key: 'annotations',

    relatedModel: Annotation,
    collectionType: AnnotationList,

    reverseRelation: {
      key: 'parentDocument',
      includeInJSON: false,
    }
  }, {
    type: 'HasMany',
    key: 'words',

    relatedModel: Word,
    collectionType: WordList,

    reverseRelation: {
      key: 'parentDocument',
      includeInJSON: false,
    }
  }],

  /* Required step after attaching YPet to a <p> to
   * extract the individual words */
  initialize: function (options) {
    var step = 0,
      space_padding,
      word_obj,
      text = options.text,
      words = _.map(_.str.words(text), function (word) {
        word_obj = {
          'text': word,
          'start': step,
        }
        space_padding = (text.substring(step).match(/\s+/g) || [""])[0].length;
        step = step + word.length + space_padding;
        return word_obj;
      });

    this.get('words').each(function (word) { word.destroy(); });
    this.get('words').add(words);
  },
});

/*
 * Views
 */
WordView = Backbone.Marionette.ItemView.extend({
  template: _.template('<% if(neighbor) { %><%= text %><% } else { %><%= text %> <% } %>'),
  tagName: 'span',

  /* These events are only triggered when over
   * a span in the paragraph */
  events: {
    'mousedown': 'mousedown',
    'mouseover': 'mouseover',
    'mouseup': 'mouseup',
  },

  /* Setup event listeners for word spans */
  initialize: function (options) {
    this.listenTo(this.model, 'change:neighbor', this.render);
    this.listenTo(this.model, 'change:latest', function (model, value, options) {
      if (this.model.get('latest')) {
        this.model.trigger('highlight', { 'color': '#FFBCBC' });
      }
      if (options.force) {
        this.model.trigger('highlight', { 'color': '#fff' });
      }
    });
    this.listenTo(this.model, 'highlight', function (options) {
      this.$el.css({ 'backgroundColor': options.color });
    });
  },

  /* Triggers the proper class assignment
   * when the word <span> is redrawn */
  onRender: function () {
    this.$el.css({ 'margin-right': this.model.get('neighbor') ? '5px' : '0px' });
  },

  /* When clicking down, make sure to keep track
   * that that word has been the latest interacted
   * element */
  mousedown: function (evt) {
    // console.log(evt, this);
    evt.stopPropagation();
    this.model.set({ 'latest': 1 });
  },

  mouseover: function (evt) {
    evt.stopPropagation();
    var word = this.model,
      words = word.collection;

    /* You're dragging if another word has a latest timestamp */
    if (_.compact(words.pluck('latest')).length) {
      if (_.isNull(word.get('latest'))) { word.set({ 'latest': Date.now() }); }

      /* If the hover doesn't proceed in ordered fashion
       * we need to "fill in the blanks" between the words */
      var current_word_idx = words.indexOf(word);
      var first_word_idx = words.indexOf(words.find(function (word) { return word.get('latest') == 1; }));

      /* Select everything from the starting to the end without
       * updating the timestamp on the first_word */
      var starting_positions = first_word_idx <= current_word_idx ? [first_word_idx, current_word_idx + 1] : [first_word_idx + 1, current_word_idx];
      var selection_indexes = _.range(_.min(starting_positions), _.max(starting_positions));
      _.each(_.without(selection_indexes, first_word_idx), function (idx) { words.at(idx).set('latest', Date.now()); });

      /* If there are extra word selections up or downstream
       * from the current selection, remove those */
      var last_selection_indexes = _.map(words.reject(function (word) { return _.isNull(word.get('latest')); }), function (word) { return words.indexOf(word); });
      var remove_indexes = _.difference(last_selection_indexes, selection_indexes);

      var word,
        ann;
      _.each(remove_indexes, function (idx) {
        word = words.at(idx);
        word.set('latest', null, { 'force': true });
        ann = word.get('parentAnnotation');
        if (ann) { ann.collection.drawAnnotations(ann); }
      });

    }
  },

  mouseup: function (evt) {
    evt.stopPropagation();
    var word = this.model,
      words = word.collection;

    var selected = words.filter(function (word) { return word.get('latest') });
    if (selected.length == 1 && word.get('parentAnnotation')) {
      word.get('parentAnnotation').toggleType();
    } else {
      /* if selection includes an annotation, delete that one */
      _.each(selected, function (w) {
        if (w.get('parentAnnotation')) {
          w.get('parentAnnotation').destroy();
        }
      })
      word.get('parentDocument').get('annotations').create({ words: selected });
    };

    words.each(function (word) { word.set('latest', null); });
  }

});

WordCollectionView = Backbone.Marionette.CollectionView.extend({
  childView: WordView,
  tagName: 'p',
  className: 'paragraph',
  events: {
    'mousedown': 'startCapture',
    'mousemove': 'startHoverCapture',
    'mouseup': 'captureAnnotation',
    'mouseleave': 'captureAnnotation',
  },

  outsideBox: function (evt) {
    var x = evt.pageX,
      y = evt.pageY;

    var obj;
    var spaces = _.compact(this.children.map(function (view) {
      obj = view.$el.offset();
      if (obj.top && obj.left) {
        obj.bottom = obj.top + view.$el.height();
        obj.right = obj.left + view.$el.width();
        return obj;
      }
    }));
    return (_.first(spaces).left > x || x > _.max(_.pluck(spaces, 'right'))) || (_.first(spaces).top > y || y > _.last(spaces).bottom);
  },

  leftBox: function (evt) {
    return evt.pageX <= this.children.first().$el.offset().left;
  },

  startCapture: function (evt) {
    var closest_view = this.getClosestWord(evt);
    if (closest_view) { closest_view.$el.trigger('mousedown'); }
  },

  timedHover: _.throttle(function (evt) {
    if (this.outsideBox(evt)) {
      var closest_view = this.getClosestWord(evt);
      if (closest_view) { closest_view.$el.trigger('mouseover'); }
    }
  }, 100),

  startHoverCapture: function (evt) { this.timedHover(evt); },

  captureAnnotation: function (evt) {
    var selection = this.collection.reject(function (word) { return _.isNull(word.get('latest')); });
    if (selection.length) {
      /* Doesn't actually matter which one */
      var model = selection[0];
      this.children.find(function (view, idx) { return model.get('start') == view.model.get('start'); }).$el.trigger('mouseup');
    }
  },

  getClosestWord: function (evt) {
    var x = evt.pageX,
      y = evt.pageY,
      closest_view = null,
      word_offset,
      dx, dy,
      distance, minDistance,
      left, top, right, bottom,
      leftBox = this.leftBox(evt);

    this.children.each(function (view, idx) {
      word_offset = view.$el.offset();
      left = word_offset.left;
      top = word_offset.top;
      right = left + view.$el.width();
      bottom = top + view.$el.height();

      if (leftBox) {
        dx = Math.abs(left - x);
      } else {
        dx = Math.abs((left + right) / 2 - x);
      }
      dy = Math.abs((top + bottom) / 2 - y);
      distance = Math.sqrt((dx * dx) + (dy * dy));

      if (minDistance === undefined || distance < minDistance) {
        minDistance = distance;
        closest_view = view;
      }

    });
    return closest_view;
  },

});

YPet = new Backbone.Marionette.Application();
// YPet.AnnotationTypes = new AnnotationTypeList([
//   { name: 'Disease', color: '#00ccff' },
//   { name: 'Gene', color: '#22A301' },
//   { name: 'Protein', color: 'yellow' }
// ]);
