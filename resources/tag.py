from flask.views import MethodView
from flask_smorest import Blueprint,abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

blp = Blueprint("Tags","tags",description="Operatsions on tags")

@blp.route("/store/<string:store_id>/tag")
class TagsInStore(MethodView):
    # return all tags for a store
    @blp.response(200,TagSchema(many=True))#response as a list
    def get(self,store_id):
        store = StoreModel.query.get_or_404(store_id)
        
        return store.tags.all()
    
    # Add a tag to a store
    @blp.arguments(TagSchema)
    @blp.response(201,TagSchema)
    def post(self,tag_data,store_id):
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data['name']).first():
            abort(400,message="A tag already exists with that name")
        tag = TagModel(**tag_data, store_id=store_id)
        
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500,message=str(e))
        
        return tag
    
@blp.route('/item/<string:item_id>/tag/<string:tag_id>')
class LinkTagsToItem(MethodView):
    @blp.response(201,TagSchema)
    def post(self,item_id,tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        if item.store.id != tag.store.id:
            abort(400, message="Make sure item and tag belong to the same store before linking.")
        
        item.tags.append(tag)
        
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500,message="An error occured while inserting the tag")
        
        return tag
    
    @blp.response(200,TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        item.tags.remove(tag)
        
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500,message="An error occured while deleting the tag")
        
        return {"message":"item removed from tag","item":item,"tag":tag}
        
        
    
@blp.route('/tags/<string:tag_id>')
class Tag(MethodView):
    #return a specific tag
    @blp.response(200,TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag
    
    @blp.response(202,description="Deletes a tag if no item is tagged with it")
    @blp.response(404, description="Tag not found")
    @blp.alt_response(400,description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        
        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message","Tag deleted."}
        abort(400,message="Could not delete tag. Make sure is not associated with any items, then try again")